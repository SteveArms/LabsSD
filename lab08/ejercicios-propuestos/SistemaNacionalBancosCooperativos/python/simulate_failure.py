"""
simulate_failure.py
============================================================
Simulación de fallos en el protocolo Two-Phase Commit (2PC).

Modos disponibles:
  --modo fallo_red      Cusco no responde en la fase PREPARE
  --modo caida_nodo     Cusco inalcanzable antes del PREPARE
  --modo recuperacion   Limpia transacciones preparadas huérfanas

Uso:
  python simulate_failure.py --modo fallo_red
  python simulate_failure.py --modo caida_nodo
  python simulate_failure.py --modo recuperacion
============================================================
"""

import sys
import time
import argparse
import psycopg2
from config import NODOS, MONTO_TRANSFERENCIA, configurar_logging

log = configurar_logging("simulate_failure")


# ─────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────

def conectar(nodo: str, autocommit: bool = False) -> psycopg2.extensions.connection:
    params = NODOS[nodo]
    conn = psycopg2.connect(**params)
    conn.autocommit = autocommit
    log.info(f"Conexión establecida con nodo '{nodo}'")
    return conn


def obtener_saldo(conn, nodo: str) -> float:
    with conn.cursor() as cur:
        cur.execute("SELECT saldo FROM cuentas LIMIT 1;")
        row = cur.fetchone()
        if row is None:
            raise RuntimeError(f"Sin cuentas en '{nodo}'")
        return float(row[0])


def ejecutar_rollback_prepared(nodo: str, gid: str) -> None:
    """Abre conexión nueva con autocommit=True y ejecuta ROLLBACK PREPARED."""
    conn = psycopg2.connect(**NODOS[nodo])
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("ROLLBACK PREPARED %s;", (gid,))
        log.warning(f"[{nodo}] ROLLBACK PREPARED '{gid}' ✓")
    finally:
        conn.close()


def mostrar_saldos_actuales() -> None:
    log.info("─── Estado actual de saldos ───────────────────────────")
    for nombre in ("arequipa", "cusco", "trujillo"):
        try:
            c = psycopg2.connect(**NODOS[nombre])
            c.autocommit = True
            with c.cursor() as cur:
                cur.execute("SELECT nombre, saldo FROM cuentas LIMIT 1;")
                row = cur.fetchone()
                if row:
                    log.info(f"  [{nombre:>9}] {row[0]}: S/ {float(row[1]):>12,.2f}")
            c.close()
        except Exception as e:
            log.warning(f"  [{nombre:>9}] No disponible: {e}")
    log.info("───────────────────────────────────────────────────────")


# ─────────────────────────────────────────────────────────────
# MODO 1: Fallo de red en la fase PREPARE
# ─────────────────────────────────────────────────────────────

def simular_fallo_red(monto: float = MONTO_TRANSFERENCIA) -> None:
    """
    Arequipa completa el PREPARE exitosamente.
    Cusco lanza excepción antes de ejecutar PREPARE (simula timeout).
    El coordinador hace ROLLBACK PREPARED solo en Arequipa.
    Resultado esperado: saldos sin cambios.
    """
    log.info("=" * 60)
    log.info("  MODO: Fallo de Red")
    log.info("  Escenario: Cusco no responde al PREPARE (timeout)")
    log.info("=" * 60)

    timestamp = int(time.time())
    gid_aqp   = f"tx_arequipa_fallo_{timestamp}"
    preparados: list[tuple[str, str]] = []

    conn_aqp = conn_cus = None

    try:
        conn_aqp = conectar("arequipa", autocommit=False)
        conn_cus = conectar("cusco",    autocommit=False)

        log.info("── FASE 1: PREPARE ─────────────────────────────────")

        # Verificar saldo
        saldo = obtener_saldo(conn_aqp, "arequipa")
        log.info(f"[arequipa] Saldo: S/ {saldo:,.2f}")

        # Débito en Arequipa
        with conn_aqp.cursor() as cur:
            cur.execute(
                "UPDATE cuentas SET saldo = saldo - %s WHERE id = 1;", (monto,)
            )
        log.info(f"[arequipa] UPDATE aplicado: -S/ {monto:,.2f}")

        # Crédito en Cusco
        with conn_cus.cursor() as cur:
            cur.execute(
                "UPDATE cuentas SET saldo = saldo + %s WHERE id = 1;", (monto,)
            )
        log.info(f"[cusco]    UPDATE aplicado: +S/ {monto:,.2f}")

        # PREPARE en Arequipa (exitoso)
        with conn_aqp.cursor() as cur:
            cur.execute(f"PREPARE TRANSACTION '{gid_aqp}';")
        preparados.append(("arequipa", gid_aqp))
        log.info(f"[arequipa] PREPARE TRANSACTION '{gid_aqp}' ✓")

        # ── FALLO SIMULADO EN CUSCO ───────────────────────────
        log.warning("[cusco]    ⚠  Simulando timeout de red — lanzando excepción...")
        raise psycopg2.OperationalError(
            "FALLO SIMULADO: Timeout de red al intentar PREPARE en Cusco"
        )

    except Exception as exc:
        log.error(f"Coordinador detectó error: {exc}")
        log.warning("── FASE 2: ROLLBACK ────────────────────────────────")

        # ROLLBACK PREPARED para los que ya se prepararon (conexión nueva)
        for nodo, gid in preparados:
            try:
                ejecutar_rollback_prepared(nodo, gid)
            except Exception as rb:
                log.error(f"[{nodo}] Error en ROLLBACK PREPARED: {rb}")

        # ROLLBACK normal para Cusco (UPDATE sin preparar)
        cusco_preparado = any(n == "cusco" for n, _ in preparados)
        if conn_cus and not conn_cus.closed and not cusco_preparado:
            try:
                conn_cus.rollback()
                log.warning("[cusco]    ROLLBACK ejecutado (UPDATE pre-PREPARE) ✓")
            except Exception:
                pass

    finally:
        for c in [conn_aqp, conn_cus]:
            if c and not c.closed:
                try:
                    c.close()
                except Exception:
                    pass

    log.info("")
    log.info("── Resultado tras fallo de red ─────────────────────────")
    mostrar_saldos_actuales()
    log.info("✅ Atomicidad preservada: saldos sin cambios.")


# ─────────────────────────────────────────────────────────────
# MODO 2: Caída de nodo (Cusco inalcanzable antes del PREPARE)
# ─────────────────────────────────────────────────────────────

def simular_caida_nodo(monto: float = MONTO_TRANSFERENCIA) -> None:
    """
    Cusco inalcanzable desde el inicio (falla la conexión TCP).
    El coordinador cancela antes de modificar cualquier dato.
    Resultado esperado: saldos sin cambios.
    """
    log.info("=" * 60)
    log.info("  MODO: Caída de Nodo")
    log.info("  Escenario: Cusco inalcanzable (nodo apagado)")
    log.info("=" * 60)

    conn_aqp = None

    try:
        conn_aqp = conectar("arequipa", autocommit=False)

        # ── FALLO SIMULADO: Cusco no responde ────────────────
        log.warning("[cusco]    ⚠  Simulando nodo caído (puerto inaccesible)...")

        params_caido = dict(NODOS["cusco"])
        params_caido["port"] = 19999        # Puerto inválido → connection refused
        params_caido["connect_timeout"] = 2

        try:
            psycopg2.connect(**params_caido)
        except psycopg2.OperationalError as e:
            raise psycopg2.OperationalError(
                f"FALLO SIMULADO: Nodo Cusco inalcanzable → {e}"
            )

    except psycopg2.OperationalError as exc:
        log.error(f"Coordinador detectó nodo caído: {exc}")
        log.warning("El 2PC se cancela antes de modificar cualquier dato.")

        if conn_aqp and not conn_aqp.closed:
            conn_aqp.rollback()
            log.warning("[arequipa] ROLLBACK ejecutado (sin cambios aplicados) ✓")

    finally:
        if conn_aqp and not conn_aqp.closed:
            conn_aqp.close()

    log.info("")
    log.info("── Resultado tras caída de nodo ────────────────────────")
    mostrar_saldos_actuales()
    log.info("✅ Atomicidad preservada: saldos sin cambios.")


# ─────────────────────────────────────────────────────────────
# MODO 3: Recuperación de transacciones huérfanas
# ─────────────────────────────────────────────────────────────

def simular_recuperacion() -> None:
    """
    Revisa pg_prepared_xacts en Arequipa y Cusco y ejecuta
    ROLLBACK PREPARED sobre cualquier transacción pendiente.
    """
    log.info("=" * 60)
    log.info("  MODO: Recuperación de Transacciones Huérfanas")
    log.info("=" * 60)

    for nombre in ("arequipa", "cusco"):
        try:
            conn = psycopg2.connect(**NODOS[nombre])
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT gid, prepared, owner FROM pg_prepared_xacts "
                    "WHERE database = current_database();"
                )
                pendientes = cur.fetchall()

            if not pendientes:
                log.info(f"[{nombre}] Sin transacciones preparadas pendientes.")
            else:
                log.warning(f"[{nombre}] {len(pendientes)} transacción(es) encontrada(s):")
                for gid, prepared_at, owner in pendientes:
                    log.warning(f"  GID='{gid}', preparada={prepared_at}, dueño={owner}")
                    with conn.cursor() as cur:
                        cur.execute("ROLLBACK PREPARED %s;", (gid,))
                    log.info(f"  → ROLLBACK PREPARED '{gid}' ✓")
            conn.close()

        except Exception as e:
            log.error(f"[{nombre}] Error durante recuperación: {e}")

    log.info("")
    log.info("── Estado final tras recuperación ─────────────────────")
    mostrar_saldos_actuales()
    log.info("✅ Recuperación completada.")


# ─────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────

MODOS = {
    "fallo_red":    simular_fallo_red,
    "caida_nodo":   simular_caida_nodo,
    "recuperacion": simular_recuperacion,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simulación de fallos 2PC - Bancos Cooperativos"
    )
    parser.add_argument(
        "--modo",
        choices=list(MODOS.keys()),
        required=True,
        help="Modo de simulación a ejecutar",
    )
    args = parser.parse_args()
    MODOS[args.modo]()
    sys.exit(0)
