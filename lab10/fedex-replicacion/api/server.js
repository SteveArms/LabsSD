// ============================================================
//  FedEx Perú — API REST
//  Demuestra: escrituras → Primary, lecturas → Replica
//  Endpoints clave para las actividades 3 y 4
// ============================================================

const express = require('express');
const { Pool } = require('pg');
const { MongoClient } = require('mongodb');
const Redis = require('ioredis');

const app = express();
app.use(express.json());

// ─────────────────────────────────────────────
// CONEXIONES — Primary para escritura, Réplica para lectura
// ─────────────────────────────────────────────
const pgWrite = new Pool({  // Lima PRIMARY
  host: process.env.PG_PRIMARY_HOST || 'localhost',
  port: 5432,
  database: 'fedex_db',
  user: 'fedex_admin',
  password: 'fedex_pass',
});

const pgRead = new Pool({   // Bogotá STANDBY (lecturas)
  host: process.env.PG_REPLICA_HOST || 'localhost',
  port: 5433,
  database: 'fedex_db',
  user: 'fedex_admin',
  password: 'fedex_pass',
});

const mongoClient = new MongoClient(
  process.env.MONGO_URI ||
  'mongodb://fedex_admin:fedex_pass@localhost:27017,localhost:27018/?replicaSet=fedexRS&authSource=admin'
);

// Redis con Sentinel para failover automático
const redis = new Redis({
  sentinels: [{ host: process.env.REDIS_SENTINEL_HOST || 'localhost', port: 26379 }],
  name: 'mymaster',
  password: 'fedex_redis',
  enableReadyCheck: false,
});

let db;

async function connectMongo() {
  await mongoClient.connect();
  db = mongoClient.db('fedex_tracking');
  console.log('MongoDB conectado al Replica Set fedexRS');
}

// ─────────────────────────────────────────────
// INVENTARIO — Lee de réplica, escribe en primary
// ─────────────────────────────────────────────

// GET /inventario?sede=LIMA
app.get('/inventario', async (req, res) => {
  try {
    const { sede } = req.query;
    const cacheKey = `inventario:${sede || 'all'}`;

    // 1. Intentar desde Redis Cache
    const cached = await redis.get(cacheKey);
    if (cached) {
      return res.json({ source: 'redis_cache', data: JSON.parse(cached) });
    }

    // 2. Leer desde réplica PostgreSQL (Bogotá)
    const query = `
      SELECT p.sku, p.nombre, i.cantidad, i.reservado,
             i.temp_min_c, i.temp_max_c, s.codigo as sede,
             i.ultima_actualizacion
      FROM inventario i
      JOIN productos p ON p.id = i.producto_id
      JOIN sedes s ON s.id = i.sede_id
      ${sede ? "WHERE s.codigo = $1" : ""}
      ORDER BY s.codigo, p.nombre
    `;
    const params = sede ? [sede] : [];
    const result = await pgRead.query(query, params);

    // 3. Guardar en cache (TTL 30s — dato semi-fresco)
    await redis.setex(cacheKey, 30, JSON.stringify(result.rows));

    res.json({ source: 'pg_replica_bogota', data: result.rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /inventario/:sede/:sku — Actualizar stock (escribe en Primary)
app.put('/inventario/:sede/:sku', async (req, res) => {
  const { sede, sku } = req.params;
  const { cantidad } = req.body;

  try {
    // Escribe en PostgreSQL Lima (PRIMARY) — síncrono con Bogotá
    const result = await pgWrite.query(`
      UPDATE inventario i
      SET cantidad = $1, ultima_actualizacion = NOW()
      FROM sedes s, productos p
      WHERE i.sede_id = s.id AND i.producto_id = p.id
        AND s.codigo = $2 AND p.sku = $3
      RETURNING i.*
    `, [cantidad, sede, sku]);

    // Invalidar caché
    await redis.del(`inventario:${sede}`).catch(() => {});

    res.json({ source: 'pg_primary_lima', updated: result.rows[0] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
// TRACKING — MongoDB asíncrono
// ─────────────────────────────────────────────

// POST /tracking — Registrar evento de envío
app.post('/tracking', async (req, res) => {
  try {
    const evento = {
      guia: req.body.guia,
      timestamp: new Date(),
      evento: req.body.evento,
      sede: req.body.sede,
      lat: req.body.lat,
      lng: req.body.lng,
      operador: req.body.operador || 'SISTEMA',
    };

    // WriteConcern w:1 → asíncrono, alta velocidad
    const col = db.collection('tracking_eventos');
    const result = await col.insertOne(evento,
      { writeConcern: { w: 1, j: false } }  // Async: no espera réplicas
    );

    // También actualizar estado en PostgreSQL (sync)
    await pgWrite.query(`
      UPDATE pedidos SET estado = $1, updated_at = NOW()
      WHERE numero_guia = $2
    `, [req.body.evento, req.body.guia]);

    res.status(201).json({ inserted: result.insertedId, evento });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /tracking/:guia
app.get('/tracking/:guia', async (req, res) => {
  try {
    const cacheKey = `tracking:${req.params.guia}`;

    // Redis primero
    const cached = await redis.get(cacheKey);
    if (cached) return res.json({ source: 'redis', data: JSON.parse(cached) });

    const col = db.collection('tracking_eventos');
    const eventos = await col
      .find({ guia: req.params.guia })
      .sort({ timestamp: -1 })
      .toArray();

    await redis.setex(cacheKey, 10, JSON.stringify(eventos)); // TTL corto: tracking es dinámico

    res.json({ source: 'mongodb_replica_set', data: eventos });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ─────────────────────────────────────────────
// HEALTH — Estado del sistema distribuido
// ─────────────────────────────────────────────
app.get('/health', async (req, res) => {
  const status = {};

  // PostgreSQL Primary
  try {
    await pgWrite.query('SELECT 1');
    const repStatus = await pgWrite.query('SELECT * FROM replication_status');
    status.pg_primary = { ok: true, replicas: repStatus.rows };
  } catch { status.pg_primary = { ok: false, error: 'Lima caído → FAILOVER activo' }; }

  // PostgreSQL Replica
  try {
    const result = await pgRead.query("SELECT pg_is_in_recovery() as is_standby, NOW() as time");
    status.pg_replica = { ok: true, is_standby: result.rows[0].is_standby };
  } catch { status.pg_replica = { ok: false }; }

  // MongoDB
  try {
    const rsStatus = await db.admin().command({ replSetGetStatus: 1 });
    status.mongodb = {
      ok: true,
      primary: rsStatus.members.find(m => m.state === 1)?.name,
      members: rsStatus.members.map(m => ({ name: m.name, state: m.stateStr }))
    };
  } catch { status.mongodb = { ok: false }; }

  // Redis
  try {
    await redis.ping();
    status.redis = { ok: true, role: 'sentinel_managed' };
  } catch { status.redis = { ok: false }; }

  res.json({ timestamp: new Date(), status });
});

// ─────────────────────────────────────────────
// ARRANQUE
// ─────────────────────────────────────────────
const PORT = process.env.PORT || 8080;

connectMongo().then(() => {
  app.listen(PORT, () => {
    console.log(`\n🚀 FedEx API corriendo en http://localhost:${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`📦 Inventario:   http://localhost:${PORT}/inventario?sede=LIMA`);
    console.log(`🚚 Tracking:     http://localhost:${PORT}/tracking/FDX-2024-001`);
  });
}).catch(console.error);
