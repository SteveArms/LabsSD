-- ==========================================================
--  FedEx Perú — Esquema PostgreSQL (Inventarios + Pedidos)
--  Ejecutado automáticamente al iniciar pg_lima
-- ==========================================================

-- Usuario de replicación
CREATE USER replicator WITH REPLICATION PASSWORD 'replicator_pass';

-- Permisos de pg_hba.conf (simulado vía env en Docker)
-- host replication replicator 0.0.0.0/0 md5

-- ──────────────────────────────────────────────────────────
--  TABLAS PRINCIPALES
-- ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sedes (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(10) UNIQUE NOT NULL,  -- LIMA, BOG, SCL, MEX
    nombre      VARCHAR(100) NOT NULL,
    pais        VARCHAR(50) NOT NULL,
    activa      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS productos (
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(50) UNIQUE NOT NULL,
    nombre          VARCHAR(200) NOT NULL,
    categoria       VARCHAR(50),   -- 'perecible', 'fragil', 'normal'
    requiere_frio   BOOLEAN DEFAULT FALSE,
    peso_kg         DECIMAL(10,3),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventario (
    id              SERIAL PRIMARY KEY,
    sede_id         INTEGER REFERENCES sedes(id),
    producto_id     INTEGER REFERENCES productos(id),
    cantidad        INTEGER NOT NULL DEFAULT 0,
    reservado       INTEGER NOT NULL DEFAULT 0,   -- cantidad en pedidos pendientes
    temp_min_c      DECIMAL(5,2),                -- temperatura requerida
    temp_max_c      DECIMAL(5,2),
    ultima_actualizacion TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(sede_id, producto_id)
);

CREATE TABLE IF NOT EXISTS clientes (
    id          SERIAL PRIMARY KEY,
    ruc         VARCHAR(20) UNIQUE,
    razon_social VARCHAR(200) NOT NULL,
    email       VARCHAR(100),
    telefono    VARCHAR(20),
    pais        VARCHAR(50),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pedidos (
    id              SERIAL PRIMARY KEY,
    numero_guia     VARCHAR(50) UNIQUE NOT NULL,
    cliente_id      INTEGER REFERENCES clientes(id),
    sede_origen_id  INTEGER REFERENCES sedes(id),
    sede_destino_id INTEGER REFERENCES sedes(id),
    estado          VARCHAR(30) DEFAULT 'CREADO',
    -- CREADO → CONFIRMADO → EN_TRANSITO → ENTREGADO | CANCELADO
    prioridad       VARCHAR(10) DEFAULT 'NORMAL', -- NORMAL, EXPRESS, CRITICO
    fecha_pedido    TIMESTAMPTZ DEFAULT NOW(),
    fecha_entrega_est TIMESTAMPTZ,
    observaciones   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS detalle_pedido (
    id          SERIAL PRIMARY KEY,
    pedido_id   INTEGER REFERENCES pedidos(id),
    producto_id INTEGER REFERENCES productos(id),
    cantidad    INTEGER NOT NULL,
    precio_unit DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS temperatura_almacen (
    id          BIGSERIAL PRIMARY KEY,
    sede_id     INTEGER REFERENCES sedes(id),
    sensor_id   VARCHAR(50),
    temperatura DECIMAL(5,2) NOT NULL,
    humedad     DECIMAL(5,2),
    alerta      BOOLEAN DEFAULT FALSE,
    registrado_at TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────────────────────────
--  ÍNDICES
-- ──────────────────────────────────────────────────────────
CREATE INDEX idx_inventario_sede ON inventario(sede_id);
CREATE INDEX idx_pedidos_estado ON pedidos(estado);
CREATE INDEX idx_pedidos_cliente ON pedidos(cliente_id);
CREATE INDEX idx_temperatura_sede_fecha ON temperatura_almacen(sede_id, registrado_at DESC);

-- ──────────────────────────────────────────────────────────
--  TRIGGER: actualizar updated_at en pedidos
-- ──────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pedidos_updated_at
    BEFORE UPDATE ON pedidos
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ──────────────────────────────────────────────────────────
--  DATOS INICIALES
-- ──────────────────────────────────────────────────────────
INSERT INTO sedes (codigo, nombre, pais) VALUES
    ('LIMA',  'Centro de Distribución Lima',            'Perú'),
    ('BOG',   'Centro de Distribución Bogotá',          'Colombia'),
    ('SCL',   'Centro de Distribución Santiago',        'Chile'),
    ('MEX',   'Centro de Distribución Ciudad de México','México');

INSERT INTO productos (sku, nombre, categoria, requiere_frio, peso_kg) VALUES
    ('PROD-001', 'Mariscos Congelados Caja 10kg',  'perecible', TRUE,  10.0),
    ('PROD-002', 'Frutas Tropicales Caja 5kg',     'perecible', TRUE,   5.0),
    ('PROD-003', 'Electrónicos - Tablet',          'fragil',    FALSE,  0.8),
    ('PROD-004', 'Medicamentos Refrigerados',       'perecible', TRUE,   2.0),
    ('PROD-005', 'Documentos Empresariales',        'normal',    FALSE,  0.1);

INSERT INTO inventario (sede_id, producto_id, cantidad, temp_min_c, temp_max_c) VALUES
    (1, 1, 500,  -20.0, -15.0),
    (1, 2, 300,    2.0,   8.0),
    (1, 3, 150,   NULL,  NULL),
    (2, 1, 400,  -20.0, -15.0),
    (2, 4, 200,    2.0,   8.0),
    (3, 2, 250,    2.0,   8.0),
    (4, 3, 180,   NULL,  NULL);

INSERT INTO clientes (ruc, razon_social, email, pais) VALUES
    ('20100123456', 'Exportadora Andina SAC',     'logistica@andina.pe',  'Perú'),
    ('900123456-7', 'Importaciones Bogotá LTDA',  'ops@bogota-imp.co',    'Colombia'),
    ('76.123.456-9','Comercial Santiago SPA',     'contacto@cstgo.cl',    'Chile'),
    ('RFC123456ABC','Distribuidora México SA',    'mexico@distrib.mx',    'México');

-- Vista para monitorear replication lag (útil en réplicas)
CREATE VIEW replication_status AS
SELECT
    application_name AS replica,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    (sent_lsn - replay_lsn) AS replication_lag_bytes,
    sync_state
FROM pg_stat_replication;
