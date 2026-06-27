#!/bin/bash
# Este script se corre dentro del contenedor pg_lima para habilitar replicación
PG_HBA="/var/lib/postgresql/data/pg_hba.conf"

# Solo agregar si no existe ya
grep -q "replication.*replicator" "$PG_HBA" || \
  echo "host replication replicator 172.20.0.0/16 md5" >> "$PG_HBA"

grep -q "all.*fedex_admin.*172.20" "$PG_HBA" || \
  echo "host all fedex_admin 172.20.0.0/16 md5" >> "$PG_HBA"

# Recargar configuración
psql -U fedex_admin -d fedex_db -c "SELECT pg_reload_conf();"
echo "pg_hba.conf actualizado correctamente"