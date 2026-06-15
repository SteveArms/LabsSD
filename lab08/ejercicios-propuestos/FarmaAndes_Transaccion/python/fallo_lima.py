import psycopg2
import time
import logging
import sys
from config import ARQUIPA_CONFIG, LIMA_CONFIG, PRODUCTO, CANTIDAD

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Excepción personalizada para simular la caída
# ─────────────────────────────────────────────
class FalloNodoError(Exception):
    """Se lanza para simular la caída de un nodo durante el 2PC."""
    pass


def limpiar_transacciones_abandonadas(conn, nodo_nombre):
    """
    Elimina transacciones preparadas que quedaron abiertas (por fallos previos).
    Reutilizada del Ejercicio 1 para garantizar un estado limpio al inicio.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT gid FROM pg_prepared_xacts")
        prepared = cur.fetchall()
        for (gid,) in prepared:
            logger.warning(f"Limpiando transaccion huerfana {gid} en {nodo_nombre}")
            cur.execute(f"ROLLBACK PREPARED '{gid}'")
        conn.commit()


def verificar_stock(conn, producto, nodo):
    """Retorna el stock actual del producto en el nodo dado."""
    with conn.cursor() as cur:
        cur.execute("SELECT stock FROM inventario WHERE producto = %s", (producto,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"{nodo}: Producto '{producto}' no existe")
        return row[0]


def preparar_transaccion(conn, tx_id, nodo):
    with conn.cursor() as cur:
        cur.execute(f"PREPARE TRANSACTION '{tx_id}'")
    logger.info(f"[FASE 1] PREPARE OK: {tx_id} en {nodo}")


def rollback_preparado(conn, tx_id, nodo):
    with conn.cursor() as cur:
        cur.execute(f"ROLLBACK PREPARED '{tx_id}'")
    logger.warning(f"[ROLLBACK] Aplicado: {tx_id} en {nodo}")


def simular_fallo_lima():
    """
    EJERCICIO 2 - Simulacion de Fallo del nodo Lima.

    Flujo intencionado:
      1. Conectar a ambos nodos.
      2. Limpiar transacciones huerfanas (estado limpio).
      3. Verificar stocks iniciales.
      4. Iniciar transaccion: descontar stock en Arequipa.
      5. FASE 1 - PREPARE en Arequipa (exitoso).
      6. Simular caida de Lima ANTES de su PREPARE  <-- fallo inyectado
      7. Detectar el fallo → ROLLBACK PREPARED en Arequipa.
      8. Verificar que ambos nodos conservan sus stocks originales.

    Resultado esperado:
      Arequipa: 100  (sin cambios)
      Lima    :  50  (sin cambios)
    """
    conn_origen = None
    conn_destino = None
    prepared = []  # lista de (conn, tx_id, nombre_nodo) que llegaron a PREPARE

    try:
        # ── 1. Conexiones ──────────────────────────────────────────────────────
        logger.info("Conectando a nodos Arequipa y Lima...")
        conn_origen = psycopg2.connect(**ARQUIPA_CONFIG)
        conn_destino = psycopg2.connect(**LIMA_CONFIG)
        conn_origen.autocommit = False
        conn_destino.autocommit = False

        # ── 2. Limpiar transacciones huerfanas de ejecuciones previas ──────────
        limpiar_transacciones_abandonadas(conn_origen, "Arequipa")
        limpiar_transacciones_abandonadas(conn_destino, "Lima")

        # ── 3. Verificar stocks iniciales ──────────────────────────────────────
        stock_orig = verificar_stock(conn_origen, PRODUCTO, "Arequipa")
        stock_dest = verificar_stock(conn_destino, PRODUCTO, "Lima")
        logger.info(f"Stock inicial -> Arequipa: {stock_orig} | Lima: {stock_dest}")

        # ── 4. Generar ID unico de transaccion distribuida ─────────────────────
        timestamp = int(time.time() * 1000)
        tx_arequipa = f"tx_fallo_areq_{timestamp}"

        # ── 5. Descontar stock en Arequipa (dentro de transaccion local) ───────
        logger.info(f"[Actividad 2] Descontando {CANTIDAD} unidades en Arequipa...")
        with conn_origen.cursor() as cur:
            cur.execute(
                "UPDATE inventario SET stock = stock - %s WHERE producto = %s",
                (CANTIDAD, PRODUCTO)
            )

        # ── 6. FASE 1: PREPARE en Arequipa ─────────────────────────────────────
        preparar_transaccion(conn_origen, tx_arequipa, "Arequipa")
        prepared.append((conn_origen, tx_arequipa, "Arequipa"))

        # ── 7. SIMULAR CAIDA DE LIMA ────────────────────────────────────────────
        #    Se lanza la excepcion ANTES de ejecutar cualquier operacion en Lima.
        #    Esto representa un fallo de red o caida del nodo destino durante el 2PC.
        logger.error("[Actividad 3] SIMULANDO CAIDA DEL NODO LIMA...")
        raise FalloNodoError("Nodo Lima no responde - conexion perdida (simulado)")

        # El codigo siguiente NUNCA se ejecuta (dead code intencional para claridad):
        # - No se hace UPDATE en Lima
        # - No se hace PREPARE en Lima
        # - No se hace COMMIT en ningun nodo

    except FalloNodoError as e:
        logger.error(f"Fallo detectado durante el 2PC: {e}")
        logger.info("[Actividad 4] Iniciando ROLLBACK de nodos que alcanzaron PREPARE...")

        # ── 8. ROLLBACK de todos los nodos que hicieron PREPARE ────────────────
        for conn, tx_id, nodo in prepared:
            try:
                rollback_preparado(conn, tx_id, nodo)
            except Exception as rb_err:
                logger.error(f"No se pudo hacer rollback de {tx_id} en {nodo}: {rb_err}")

        # ── 9. Verificar que los stocks quedaron intactos ──────────────────────
        try:
            stock_final_areq = verificar_stock(conn_origen, PRODUCTO, "Arequipa")
            stock_final_lima = verificar_stock(conn_destino, PRODUCTO, "Lima")
            logger.info("─" * 55)
            logger.info("RESULTADO FINAL (rollback completado):")
            logger.info(f"  Arequipa: {stock_final_areq}  (esperado: {stock_orig})")
            logger.info(f"  Lima    : {stock_final_lima}  (esperado: {stock_dest})")

            consistente = (stock_final_areq == stock_orig and
                           stock_final_lima == stock_dest)
            if consistente:
                logger.info("CONSISTENCIA OK: ambos nodos conservan el stock original.")
            else:
                logger.error("INCONSISTENCIA DETECTADA: los stocks no coinciden con los valores originales.")
            logger.info("─" * 55)
        except Exception as verify_err:
            logger.error(f"No se pudo verificar el estado final: {verify_err}")

        sys.exit(1)

    except Exception as e:
        # Cualquier otro error inesperado
        logger.error(f"Error inesperado: {e}")
        for conn, tx_id, nodo in prepared:
            try:
                rollback_preparado(conn, tx_id, nodo)
            except Exception as rb_err:
                logger.error(f"No se pudo hacer rollback de {tx_id} en {nodo}: {rb_err}")
        sys.exit(1)

    finally:
        if conn_origen:
            conn_origen.close()
        if conn_destino:
            conn_destino.close()


if __name__ == "__main__":
    simular_fallo_lima()
