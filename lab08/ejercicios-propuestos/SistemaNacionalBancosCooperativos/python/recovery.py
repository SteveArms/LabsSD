"""
recovery.py
============================================================
Herramienta independiente de recuperación ante fallos.

Propósito: limpiar transacciones preparadas (PREPARE TRANSACTION)
que quedaron huérfanas por fallo del coordinador o de la red,
impidiendo que los recursos permanezcan bloqueados indefinidamente.

Funcionalidades:
  - Listar transacciones preparadas en todos los nodos
  - Hacer ROLLBACK PREPARED sobre transacciones huérfanas
  - Verificar consistencia global tras la limpieza
  - Opcionalmente forzar COMMIT PREPARED (si el contexto lo permite)

Uso:
  python recovery.py                        # Modo interactivo
  python recovery.py --accion listar        # Solo listar
  python recovery.py --accion rollback_todo # Rollback de todas
  python recovery.py --accion verificar     # Solo verificar consistencia
============================================================
"""

import sys
import argparse
import psycopg2
from config import NODOS, configurar_logging

log = configurar_logging("recovery")


# ─────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────

def conectar_autocommit(nodo: str) -> psycopg2.extensions.connection | None:
    """Conecta al nodo en modo autocommit. Retorna None si falla."""
    try:
        conn = psycopg2.connect(**NODOS[nodo])
        conn.autocommit = True
        return conn
    except psycopg2.OperationalError as e:
        log.error(f"[{nodo}] No se pudo conectar: {e}")
        return None


def listar_preparadas(conn, nodo: str) -> list[dict]:
    """
    Consulta pg_prepared_xacts y devuelve las transacciones
    preparadas en la base de datos actual.
    """
    resultado = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT gid, prepared, owner, database
                FROM   pg_prepared_xacts
                WHERE  database = current_database()
                ORDER  BY prepared;
                """
            )
            filas = cur.fetchall()
            for gid, prepared_at, owner, database in filas:
                resultado.append({
                    "gid":         gid,
                    "prepared_at": prepared_at,
                    "owner":       owner,
                    "database":    database,
                    "nodo":        nodo,
                })
    except Exception as e:
        log.error(f"[{nodo}] Error consultando pg_prepared_xacts: {e}")
    return resultado


def rollback_prepared(conn, gid: str, nodo: str) -> bool:
    """Ejecuta ROLLBACK PREPARED para el GID indicado."""
    try:
        with conn.cursor() as cur:
            cur.execute("ROLLBACK PREPARED %s;", (gid,))
        log.info(f"[{nodo}] ROLLBACK PREPARED '{gid}' ✓")
        return True
    except Exception as e:
        log.error(f"[{nodo}] Error en ROLLBACK PREPARED '{gid}': {e}")
        return False


def commit_prepared(conn, gid: str, nodo: str) -> bool:
    """
    Ejecuta COMMIT PREPARED para el GID indicado.
    Usar solo cuando se tiene certeza de que TODOS los participantes
    llegaron a PREPARE correctamente.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("COMMIT PREPARED %s;", (gid,))
        log.info(f"[{nodo}] COMMIT PREPARED '{gid}' ✓")
        return True
    except Exception as e:
        log.error(f"[{nodo}] Error en COMMIT PREPARED '{gid}': {e}")
        return False


# ─────────────────────────────────────────────────────────────
# Verificación de consistencia global
# ─────────────────────────────────────────────────────────────

def verificar_consistencia_global() -> None:
    """
    Lee el saldo actual de cada nodo y muestra la suma total.
    La suma debe ser siempre S/ 225,000 (100k + 50k + 75k).
    """
    log.info("─── Verificación de consistencia global ───────────────")
    suma = 0.0
    for nombre in ("arequipa", "cusco", "trujillo"):
        conn = conectar_autocommit(nombre)
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT nombre, saldo FROM cuentas LIMIT 1;")
                    row = cur.fetchone()
                    if row:
                        saldo = float(row[1])
                        suma += saldo
                        log.info(f"  [{nombre:>9}] {row[0]}: S/ {saldo:>12,.2f}")
                    else:
                        log.warning(f"  [{nombre:>9}] Sin datos en la tabla 'cuentas'.")
            except Exception as e:
                log.error(f"  [{nombre:>9}] Error leyendo saldo: {e}")
            finally:
                conn.close()
        else:
            log.warning(f"  [{nombre:>9}] NODO NO DISPONIBLE")

    log.info(f"  {'TOTAL':>10}: S/ {suma:>12,.2f}  (esperado: S/ 225,000.00)")
    if abs(suma - 225_000.0) < 0.01:
        log.info("✅ Consistencia global PRESERVADA.")
    else:
        log.error("❌ Inconsistencia detectada. Revisar logs de transacciones.")
    log.info("───────────────────────────────────────────────────────")


# ─────────────────────────────────────────────────────────────
# Acciones principales
# ─────────────────────────────────────────────────────────────

def accion_listar() -> dict[str, list[dict]]:
    """Lista todas las transacciones preparadas en todos los nodos."""
    log.info("=" * 60)
    log.info("  ACCIÓN: Listar transacciones preparadas pendientes")
    log.info("=" * 60)
    reporte: dict[str, list[dict]] = {}

    for nombre in ("arequipa", "cusco", "trujillo"):
        conn = conectar_autocommit(nombre)
        if conn is None:
            reporte[nombre] = []
            continue
        try:
            txs = listar_preparadas(conn, nombre)
            reporte[nombre] = txs
            if txs:
                log.warning(f"[{nombre}] {len(txs)} transacción(es) preparada(s):")
                for tx in txs:
                    log.warning(
                        f"  GID='{tx['gid']}' | "
                        f"preparada={tx['prepared_at']} | "
                        f"dueño={tx['owner']}"
                    )
            else:
                log.info(f"[{nombre}] Sin transacciones preparadas pendientes.")
        finally:
            conn.close()

    return reporte


def accion_rollback_todo() -> None:
    """Hace ROLLBACK PREPARED sobre TODAS las transacciones huérfanas."""
    log.info("=" * 60)
    log.info("  ACCIÓN: Rollback de todas las transacciones huérfanas")
    log.info("=" * 60)
    reporte = accion_listar()

    total_rollbacks = 0
    for nombre, txs in reporte.items():
        if not txs:
            continue
        conn = conectar_autocommit(nombre)
        if conn is None:
            log.error(f"[{nombre}] Nodo no disponible, no se pudo limpiar.")
            continue
        try:
            for tx in txs:
                exito = rollback_prepared(conn, tx["gid"], nombre)
                if exito:
                    total_rollbacks += 1
        finally:
            conn.close()

    log.info("")
    if total_rollbacks == 0:
        log.info("No había transacciones huérfanas que limpiar.")
    else:
        log.info(f"Se realizaron {total_rollbacks} ROLLBACK PREPARED.")

    log.info("")
    verificar_consistencia_global()


def accion_verificar() -> None:
    """Solo verifica la consistencia global, sin modificar nada."""
    log.info("=" * 60)
    log.info("  ACCIÓN: Verificar consistencia global")
    log.info("=" * 60)
    verificar_consistencia_global()


def accion_interactiva() -> None:
    """Modo interactivo: muestra el estado y pregunta qué hacer."""
    log.info("=" * 60)
    log.info("  MODO INTERACTIVO - Recovery Tool")
    log.info("=" * 60)

    reporte = accion_listar()
    total_pendientes = sum(len(v) for v in reporte.values())

    if total_pendientes == 0:
        log.info("No hay transacciones pendientes. Verificando consistencia...")
        verificar_consistencia_global()
        return

    log.info(f"\nSe encontraron {total_pendientes} transacción(es) huérfana(s).")
    respuesta = input("¿Desea hacer ROLLBACK de todas? (s/N): ").strip().lower()

    if respuesta == "s":
        for nombre, txs in reporte.items():
            if not txs:
                continue
            conn = conectar_autocommit(nombre)
            if conn is None:
                continue
            try:
                for tx in txs:
                    rollback_prepared(conn, tx["gid"], nombre)
            finally:
                conn.close()
        log.info("Limpieza completada.")
    else:
        log.info("No se realizaron cambios.")

    verificar_consistencia_global()


# ─────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────

ACCIONES = {
    "listar":        accion_listar,
    "rollback_todo": accion_rollback_todo,
    "verificar":     accion_verificar,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Herramienta de recuperación 2PC - Bancos Cooperativos"
    )
    parser.add_argument(
        "--accion",
        choices=list(ACCIONES.keys()),
        default=None,
        help=(
            "listar: mostrar transacciones pendientes | "
            "rollback_todo: limpiar todas | "
            "verificar: comprobar consistencia global"
        ),
    )
    args = parser.parse_args()

    if args.accion is None:
        accion_interactiva()
    else:
        ACCIONES[args.accion]()

    sys.exit(0)
