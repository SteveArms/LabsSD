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

def limpiar_transacciones_abandonadas(conn, nodo_nombre):
    """
    Elimina transacciones preparadas que quedaron abiertas (por fallos previos).
    """
    with conn.cursor() as cur:
        cur.execute("SELECT gid FROM pg_prepared_xacts")
        prepared = cur.fetchall()
        for (gid,) in prepared:
            logger.warning(f"Limpiando transaccion huérfana {gid} en {nodo_nombre}")
            cur.execute(f"ROLLBACK PREPARED '{gid}'")
        conn.commit()

def verificar_stock(conn, producto, cantidad, nodo):
    with conn.cursor() as cur:
        cur.execute("SELECT stock FROM inventario WHERE producto = %s", (producto,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"{nodo}: Producto '{producto}' no existe")
        stock = row[0]
        if stock < cantidad:
            raise ValueError(f"{nodo}: Stock insuficiente ({stock} < {cantidad})")
        return stock

def verificar_consistencia_total(conn_origen, conn_destino, producto):
    """
    Verifica que la suma de stocks entre nodos sea la misma antes y después.
    """
    with conn_origen.cursor() as cur_o, conn_destino.cursor() as cur_d:
        cur_o.execute("SELECT stock FROM inventario WHERE producto = %s", (producto,))
        cur_d.execute("SELECT stock FROM inventario WHERE producto = %s", (producto,))
        stock_o = cur_o.fetchone()[0]
        stock_d = cur_d.fetchone()[0]
        return stock_o + stock_d

def preparar_transaccion(conn, tx_id, nodo):
    with conn.cursor() as cur:
        cur.execute(f"PREPARE TRANSACTION '{tx_id}'")
    logger.info(f"Preparado: {tx_id} en {nodo}")

def commit_preparado(conn, tx_id, nodo):
    with conn.cursor() as cur:
        cur.execute(f"COMMIT PREPARED '{tx_id}'")
    logger.info(f"Commit confirmado: {tx_id} en {nodo}")

def rollback_preparado(conn, tx_id, nodo):
    with conn.cursor() as cur:
        cur.execute(f"ROLLBACK PREPARED '{tx_id}'")
    logger.warning(f"Rollback aplicado: {tx_id} en {nodo}")

def transferir():
    conn_origen = None
    conn_destino = None
    prepared = []   # (conn, tx_id, nombre_nodo)

    try:
        # 1. Conexiones
        conn_origen = psycopg2.connect(**ARQUIPA_CONFIG)
        conn_destino = psycopg2.connect(**LIMA_CONFIG)
        conn_origen.autocommit = False
        conn_destino.autocommit = False

        # 2. Limpiar transacciones previas huérfanas
        limpiar_transacciones_abandonadas(conn_origen, "Arequipa")
        limpiar_transacciones_abandonadas(conn_destino, "Lima")

        # 3. Verificar stock disponible (fuera de la transacción para evitar bloqueos innecesarios)
        stock_orig = verificar_stock(conn_origen, PRODUCTO, CANTIDAD, "Arequipa")
        logger.info(f"Stock en Arequipa antes: {stock_orig}")
        # También podemos registrar stock en Lima para referencia
        stock_dest = verificar_stock(conn_destino, PRODUCTO, 0, "Lima")  # solo lectura
        logger.info(f"Stock en Lima antes: {stock_dest}")

        # 4. Generar IDs únicos para la transacción distribuida
        timestamp = int(time.time() * 1000)  # milisegundos
        tx_arequipa = f"tx_areq_{timestamp}"
        tx_lima = f"tx_lim_{timestamp}"

        # 5. Ejecutar las actualizaciones dentro de transacciones locales
        with conn_origen.cursor() as cur:
            cur.execute(
                "UPDATE inventario SET stock = stock - %s WHERE producto = %s",
                (CANTIDAD, PRODUCTO)
            )
        with conn_destino.cursor() as cur:
            cur.execute(
                "UPDATE inventario SET stock = stock + %s WHERE producto = %s",
                (CANTIDAD, PRODUCTO)
            )

        # 6. FASE 1: PREPARE en ambos nodos
        preparar_transaccion(conn_origen, tx_arequipa, "Arequipa")
        prepared.append((conn_origen, tx_arequipa, "Arequipa"))
        preparar_transaccion(conn_destino, tx_lima, "Lima")
        prepared.append((conn_destino, tx_lima, "Lima"))

        # 7. FASE 2: COMMIT PREPARED en ambos
        for conn, tx_id, nodo in prepared:
            commit_preparado(conn, tx_id, nodo)

        # 8. Verificación final de consistencia
        suma_final = verificar_consistencia_total(conn_origen, conn_destino, PRODUCTO)
        suma_inicial = stock_orig + stock_dest
        if suma_final != suma_inicial:
            raise RuntimeError(f"Inconsistencia: suma inicial {suma_inicial} != suma final {suma_final}")

        logger.info(f"Transferencia exitosa: {CANTIDAD} unidades de {PRODUCTO} de Arequipa a Lima")
        logger.info(f"Stock final Arequipa: {stock_orig - CANTIDAD}, Lima: {stock_dest + CANTIDAD}")

    except Exception as e:
        logger.error(f"Fallo en la transferencia: {e}")
        # Rollback de los nodos que ya hayan hecho PREPARE
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
    transferir()