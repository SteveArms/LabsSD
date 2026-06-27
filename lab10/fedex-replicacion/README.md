# 🏢 FedEx Perú — Replicación Distribuida
## Sistemas Distribuidos | Actividades 1–4

---

## 📁 Estructura del Proyecto

```
fedex-replicacion/
├── docker-compose.yml          ← Infraestructura completa
├── init-scripts/
│   └── pg/
│       └── 01_schema.sql       ← Esquema PostgreSQL + datos iniciales
├── api/
│   ├── server.js               ← API REST Node.js
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── init-replication.sh     ← Inicializar replica sets
│   └── simulate_failover.sh    ← Simular caída de Lima (Actividad 4)
└── monitoring/
    └── prometheus.yml
```

---

## 🚀 Instrucciones de Ejecución

### Requisitos
- Docker Desktop instalado y corriendo
- Puertos libres: 5432-5434, 27017-27019, 6379-6380, 3000, 8080, 9090

### Paso 1 — Levantar infraestructura
```bash
docker compose up -d
```

### Paso 2 — Inicializar replicación
```bash
chmod +x scripts/*.sh
bash scripts/init-replication.sh
```

### Paso 3 — Verificar que todo funciona
```bash
# Ver estado de replicación PostgreSQL
docker exec pg_lima_primary psql -U fedex_admin -d fedex_db \
  -c "SELECT * FROM replication_status;"

# Ver estado MongoDB Replica Set
docker exec mongo_lima_primary mongosh --quiet \
  --eval "rs.status().members.forEach(m => print(m.name, m.stateStr))"

# Test API
curl http://localhost:8080/health
curl "http://localhost:8080/inventario?sede=LIMA"
curl http://localhost:8080/tracking/FDX-2024-001
```

### Paso 4 — Simular fallo Lima (Actividad 4)
```bash
bash scripts/simulate_failover.sh
```

---

## 🔗 Interfaces

| Servicio | URL | Credenciales |
|---------|-----|-------------|
| API FedEx | http://localhost:8080 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| PostgreSQL Lima | localhost:5432 | fedex_admin / fedex_pass |
| PostgreSQL Bogotá | localhost:5433 | fedex_admin / fedex_pass |
| MongoDB | localhost:27017 | fedex_admin / fedex_pass |

---

## 📊 Verificar Replicación en DBeaver / pgAdmin

Conectar a **localhost:5432** (Lima Primary) y ejecutar:
```sql
-- Ver réplicas conectadas y lag
SELECT * FROM replication_status;

-- Ver últimas temperaturas registradas
SELECT * FROM temperatura_almacen ORDER BY registrado_at DESC LIMIT 10;

-- Ver pedidos críticos
SELECT numero_guia, estado, prioridad, fecha_pedido
FROM pedidos WHERE prioridad = 'CRITICO';
```

Conectar a **localhost:5433** (Bogotá Standby) y ejecutar las mismas queries
→ debe mostrar los mismos datos (replicación síncrona).

---

## 🏗️ Arquitectura Implementada

Ver `arquitectura_fedex.md` para diagrama completo en Mermaid.

| Tecnología | Rol | Tipo Replicación |
|-----------|-----|-----------------|
| PostgreSQL | Inventarios + Pedidos | **Síncrona** Lima→Bogotá / Asíncrona →Santiago/México |
| MongoDB | Tracking + GPS | Asíncrona (Replica Set) |
| Redis | Caché + Sesiones | Asíncrona (Master-Replica + Sentinel) |
| Prometheus/Grafana | Monitoreo | — |
