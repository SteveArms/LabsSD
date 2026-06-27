#!/bin/bash
# =============================================================
#  FedEx Perú — Script de Inicialización de Replicación
#  Ejecutar DESPUÉS de: docker compose up -d
# =============================================================

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${YELLOW}══════════════════════════════════════════${NC}"
echo -e "${YELLOW}  FedEx Perú — Init Replicación Distribuida${NC}"
echo -e "${YELLOW}══════════════════════════════════════════${NC}"

# ── 1. ESPERAR POSTGRESQL LIMA ──────────────────────────────
echo -e "\n${YELLOW}[1/5] Esperando PostgreSQL Lima...${NC}"
until docker exec pg_lima_primary pg_isready -U fedex_admin -d fedex_db &>/dev/null; do
  printf "."; sleep 2
done
echo -e "\n${GREEN}  ✅ PostgreSQL Lima activo${NC}"

# ── 2. CONFIGURAR pg_hba.conf ───────────────────────────────
echo -e "\n${YELLOW}[2/5] Configurando pg_hba para replicación...${NC}"
docker exec pg_lima_primary bash -c "
  grep -q 'replicator' /var/lib/postgresql/data/pg_hba.conf || \
    echo 'host replication replicator 172.20.0.0/16 md5' >> /var/lib/postgresql/data/pg_hba.conf
  grep -q '172.20.0.0/16' /var/lib/postgresql/data/pg_hba.conf || \
    echo 'host all all 172.20.0.0/16 md5' >> /var/lib/postgresql/data/pg_hba.conf
  psql -U fedex_admin -d fedex_db -c \"SELECT pg_reload_conf();\" -q
"
echo -e "${GREEN}  ✅ pg_hba.conf actualizado${NC}"

# ── 3. LEVANTAR STANDBYS POSTGRESQL ─────────────────────────
echo -e "\n${YELLOW}[3/5] Levantando standbys PostgreSQL (Bogotá + Santiago)...${NC}"
docker compose --profile standbys up -d 2>/dev/null || true
echo -e "${YELLOW}  ⏳ Esperando que los standby sincronicen (30s)...${NC}"
sleep 30

# Verificar
PG_BOG_OK=$(docker exec pg_bogota_standby pg_isready -U fedex_admin 2>/dev/null && echo "OK" || echo "FAIL")
echo -e "${GREEN}  Bogotá standby: ${PG_BOG_OK}${NC}"

# ── 4. INICIALIZAR MONGODB REPLICA SET ──────────────────────
echo -e "\n${YELLOW}[4/5] Inicializando MongoDB Replica Set fedexRS...${NC}"
sleep 5

docker exec mongo_lima_primary mongosh --quiet --eval "
try {
  rs.status();
  print('ReplicaSet ya inicializado');
} catch(e) {
  rs.initiate({
    _id: 'fedexRS',
    members: [
      { _id: 0, host: '172.20.0.20:27017', priority: 10 },
      { _id: 1, host: '172.20.0.21:27017', priority: 5  },
      { _id: 2, host: '172.20.0.22:27017', priority: 1  }
    ]
  });
  print('ReplicaSet inicializado');
}
" 2>/dev/null

sleep 5

# Crear colecciones y datos de prueba
docker exec mongo_lima_primary mongosh --quiet --eval "
use fedex_tracking;
db.tracking_eventos.drop();
db.tracking_eventos.insertMany([
  { guia: 'FDX-2024-001', timestamp: new Date(), evento: 'RECIBIDO',    sede: 'LIMA', lat: -12.046374, lng: -77.042793 },
  { guia: 'FDX-2024-001', timestamp: new Date(), evento: 'EN_ALMACEN',  sede: 'LIMA', lat: -12.046374, lng: -77.042793 },
  { guia: 'FDX-2024-002', timestamp: new Date(), evento: 'EN_TRANSITO', sede: 'BOG',  lat:   4.710989, lng:  -74.072092 },
  { guia: 'FDX-2024-003', timestamp: new Date(), evento: 'ENTREGADO',   sede: 'SCL',  lat: -33.459229, lng:  -70.645348 }
]);
db.vehiculos_gps.drop();
db.vehiculos_gps.insertMany([
  { placa: 'ABC-123', sede: 'LIMA', lat: -12.05, lng: -77.04, velocidad_kmh: 65, timestamp: new Date() },
  { placa: 'XYZ-456', sede: 'BOG',  lat:   4.71, lng: -74.07, velocidad_kmh: 45, timestamp: new Date() }
]);
print('Datos MongoDB insertados');
" 2>/dev/null

echo -e "${GREEN}  ✅ MongoDB Replica Set fedexRS inicializado${NC}"

# ── 5. VERIFICAR REDIS + LEVANTAR API ───────────────────────
echo -e "\n${YELLOW}[5/5] Verificando Redis y levantando API...${NC}"
REDIS_ROLE=$(docker exec redis_lima_master redis-cli -a fedex_redis INFO replication 2>/dev/null | grep "role:" | tr -d '\r\n ')
REPLICAS=$(docker exec redis_lima_master redis-cli -a fedex_redis INFO replication 2>/dev/null | grep "connected_slaves:" | tr -d '\r\n ')
echo -e "${GREEN}  ✅ Redis Lima: ${REDIS_ROLE} | ${REPLICAS}${NC}"

docker compose --profile app up -d 2>/dev/null || true
sleep 5

# ── RESUMEN ──────────────────────────────────────────────────
echo -e "\n${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Infraestructura FedEx lista${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""
echo "  🐘 PostgreSQL Lima     → localhost:5432  (PRIMARY)"
echo "  🐘 PostgreSQL Bogotá   → localhost:5433  (SYNC standby)"
echo "  🐘 PostgreSQL Santiago → localhost:5434  (ASYNC standby)"
echo "  🍃 MongoDB Lima        → localhost:27017 (PRIMARY)"
echo "  🍃 MongoDB Bogotá      → localhost:27018 (SECONDARY)"
echo "  🍃 MongoDB Santiago    → localhost:27019 (SECONDARY)"
echo "  🔴 Redis Lima          → localhost:6379  (MASTER)"
echo "  🔴 Redis Bogotá        → localhost:6380  (REPLICA)"
echo "  📊 Grafana             → http://localhost:3000  (admin/admin)"
echo "  📈 Prometheus          → http://localhost:9090"
echo "  🚀 API FedEx           → http://localhost:8080"
echo ""
echo -e "${YELLOW}  Verificar replicación PG:${NC}"
echo "  docker exec pg_lima_primary psql -U fedex_admin -d fedex_db -c 'SELECT * FROM replication_status;'"
echo ""
echo -e "${YELLOW}  Test rápido API:${NC}"
echo "  curl http://localhost:8080/health"
echo "  curl 'http://localhost:8080/inventario?sede=LIMA'"
echo ""
echo -e "${YELLOW}  Simular fallo Lima (Actividad 4):${NC}"
echo "  bash scripts/simulate_failover.sh"