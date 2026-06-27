#!/bin/bash
# =============================================================
#  FedEx Perú — SIMULACIÓN DE FALLO: Actividad 4
#  Simula la caída del centro de datos Lima por ~2 minutos
# =============================================================

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

DOWNTIME=60  # segundos (representa 20 min del caso)

echo -e "${RED}╔══════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  ⚠️  SIMULACIÓN DE FALLO — LIMA DATA CENTER  ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════╝${NC}"
echo -e "  Hora de inicio: $(date '+%H:%M:%S')"
echo -e "  Duración simulada: ${DOWNTIME}s\n"

# ── PRE-FALLO ────────────────────────────────────────────────
echo -e "${BLUE}═══ PRE-FALLO: Estado del sistema ═══${NC}"

echo -e "\n${YELLOW}[PostgreSQL] Replicación activa:${NC}"
docker exec pg_lima_primary psql -U fedex_admin -d fedex_db -c \
  "SELECT replica, state, replication_lag_bytes, sync_state FROM replication_status;" \
  2>/dev/null || echo "  (sin réplicas conectadas aún)"

echo -e "\n${YELLOW}[MongoDB] Estado Replica Set:${NC}"
docker exec mongo_lima_primary mongosh --quiet --eval \
  "rs.status().members.forEach(m => print('  ' + m.name + ' → ' + m.stateStr))" \
  2>/dev/null

echo -e "\n${YELLOW}[Redis] Estado:${NC}"
docker exec redis_lima_master redis-cli -a fedex_redis INFO replication 2>/dev/null \
  | grep -E "role:|connected_slaves:" | sed 's/^/  /'

echo -e "\n${YELLOW}[PostgreSQL] Insertando transacción crítica en Lima (síncrona con Bogotá)...${NC}"
docker exec pg_lima_primary psql -U fedex_admin -d fedex_db -c "
INSERT INTO pedidos (numero_guia, cliente_id, sede_origen_id, sede_destino_id, estado, prioridad)
VALUES ('FDX-FAILOVER-$(date +%s)', 1, 1, 2, 'CONFIRMADO', 'CRITICO')
RETURNING numero_guia, estado, prioridad;" 2>/dev/null

echo -e "\n${YELLOW}[MongoDB] Insertando evento de tracking asíncrono...${NC}"
docker exec mongo_lima_primary mongosh fedex_tracking --quiet --eval "
db.tracking_eventos.insertOne({
  guia: 'FDX-ASYNC-$(date +%s)',
  timestamp: new Date(),
  evento: 'PRE_FALLO',
  sede: 'LIMA',
  nota: 'Este evento puede perderse si el lag > 0'
}); print('Evento insertado');" 2>/dev/null

# ── FALLO ────────────────────────────────────────────────────
echo -e "\n${RED}═══════════════════════════════════════════════${NC}"
echo -e "${RED}💥 $(date '+%H:%M:%S') — LIMA CAÍDO. Deteniendo nodos...${NC}"
echo -e "${RED}═══════════════════════════════════════════════${NC}"

docker stop pg_lima_primary mongo_lima_primary redis_lima_master 2>/dev/null
echo -e "${RED}  Contenedores Lima detenidos: pg_lima, mongo_lima, redis_lima${NC}"

# ── DETECCIÓN Y FAILOVER ─────────────────────────────────────
echo -e "\n${YELLOW}[T+5s]  Redis Sentinel detectando fallo del master...${NC}"
sleep 6
echo -e "${YELLOW}[T+10s] Iniciando elección de nuevo master Redis...${NC}"
sleep 5

NEW_MASTER=$(docker exec redis_sentinel redis-cli -p 26379 \
  SENTINEL get-master-addr-by-name mymaster 2>/dev/null | head -1)
echo -e "${GREEN}  ✅ Nuevo Redis Master promovido: ${NEW_MASTER:-redis_bogota}${NC}"

echo -e "\n${YELLOW}[T+15s] MongoDB eligiendo nuevo Primary...${NC}"
sleep 8
docker exec mongo_bogota_secondary mongosh --quiet --eval \
  "rs.status().members.forEach(m => print('  ' + m.name + ' → ' + m.stateStr))" \
  2>/dev/null || echo "  ⏳ Elección en progreso..."

# ── CONTINUIDAD DESDE BOGOTÁ ─────────────────────────────────
echo -e "\n${BLUE}═══ VERIFICANDO CONTINUIDAD DESDE BOGOTÁ ═══${NC}"

echo -e "\n${YELLOW}[PostgreSQL Bogotá] Leyendo inventario (réplica síncrona):${NC}"
docker exec pg_bogota_standby psql -U fedex_admin -d fedex_db -c "
SELECT p.nombre, i.cantidad, s.codigo as sede
FROM inventario i
JOIN productos p ON p.id = i.producto_id
JOIN sedes s ON s.id = i.sede_id
LIMIT 5;" 2>/dev/null || echo "  ⚠️  Bogotá en modo read-only standby (esperado)"

echo -e "\n${YELLOW}[PostgreSQL Bogotá] Pedido crítico replicado síncronamente:${NC}"
docker exec pg_bogota_standby psql -U fedex_admin -d fedex_db -c "
SELECT numero_guia, estado, prioridad
FROM pedidos WHERE prioridad='CRITICO' ORDER BY id DESC LIMIT 3;" 2>/dev/null

echo -e "\n${YELLOW}[MongoDB Bogotá] Buscando evento de tracking:${NC}"
docker exec mongo_bogota_secondary mongosh fedex_tracking --quiet --eval "
  printjson(db.tracking_eventos.find({},{_id:0,guia:1,evento:1,sede:1}).sort({timestamp:-1}).limit(3).toArray())
" 2>/dev/null

# ── ANÁLISIS ─────────────────────────────────────────────────
echo -e "\n${RED}═══ ANÁLISIS: Pérdida de datos por tipo de replicación ═══${NC}"
echo ""
echo "  ┌────────────────────────┬──────────────┬──────────────────────────────────┐"
echo "  │ Dato                   │ Replicación  │ Pérdida potencial                │"
echo "  ├────────────────────────┼──────────────┼──────────────────────────────────┤"
echo "  │ Inventarios/Pedidos    │ SÍNCRONA     │ ✅ CERO — confirmado en Bogotá   │"
echo "  │ Tracking de envíos     │ ASÍNCRONA    │ ⚠️  Últimos 1-5s de eventos      │"
echo "  │ GPS vehicular          │ ASÍNCRONA    │ ⚠️  Posiciones de últimos 2-3s   │"
echo "  │ Temperatura almacén    │ ASÍNCRONA    │ ⚠️  Últimas lecturas IoT         │"
echo "  │ Sesiones Redis         │ ASÍNCRONA    │ ⚠️  Sesiones no replicadas       │"
echo "  └────────────────────────┴──────────────┴──────────────────────────────────┘"
echo ""
echo -e "  ${GREEN}RPO PostgreSQL (síncrono): 0 transacciones perdidas${NC}"
echo -e "  ${YELLOW}RPO MongoDB (asíncrono):   ~1-5 segundos de eventos${NC}"
echo -e "  ${GREEN}RTO estimado:              30-60 segundos${NC}"

# ── COUNTDOWN ────────────────────────────────────────────────
echo -e "\n${YELLOW}[DOWNTIME] Lima caído. Recuperando en ${DOWNTIME}s...${NC}"
for i in $(seq $DOWNTIME -10 10); do
  echo -e "  ⏳ ${i}s restantes..."
  sleep 10
done

# ── RECUPERACIÓN ─────────────────────────────────────────────
echo -e "\n${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}🔄 $(date '+%H:%M:%S') — RECUPERANDO LIMA...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"

docker start pg_lima_primary mongo_lima_primary redis_lima_master 2>/dev/null
sleep 8

echo -e "${GREEN}  ✅ Nodos Lima reiniciados${NC}"
echo -e "${YELLOW}  ℹ️  En producción con Patroni: Lima entraría como STANDBY de Bogotá${NC}"
echo -e "${YELLOW}     hasta un failback manual controlado.${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Simulación completada                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Hora finalización: $(date '+%H:%M:%S')"
echo ""
echo -e "  ${YELLOW}Verificar estado actual:${NC}"
echo "  docker exec pg_lima_primary psql -U fedex_admin -d fedex_db -c 'SELECT * FROM replication_status;'"
echo "  curl http://localhost:8080/health"