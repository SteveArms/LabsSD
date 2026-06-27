-- Crear usuario de replicación (ejecutado automáticamente al iniciar pg_lima)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'replicator') THEN
    CREATE USER replicator WITH REPLICATION PASSWORD 'replicator_pass';
  END IF;
END
$$;

-- Dar permisos de conexión
GRANT CONNECT ON DATABASE fedex_db TO replicator;