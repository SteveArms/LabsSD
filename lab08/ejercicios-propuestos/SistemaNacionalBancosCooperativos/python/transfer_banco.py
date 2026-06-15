"""
transfer_banco.py
============================================================
Coordinador del protocolo Two-Phase Commit (2PC).

Escenario: Transferencia exitosa de S/ 25,000
           desde el nodo Arequipa hacia el nodo Cusco.

Flujo 2PC:
  FASE 1 - PREPARE:
    1. Conectar a Arequipa y Cusco (autocommit=False)
    2. Verificar saldo suficiente en Arequipa
    3. Aplicar débito en Arequipa (UPDATE)
    4. Aplicar crédito en Cusco   (UPDATE)
    5. PREPARE TRANSACTION en Arequipa
    6. PREPARE TRANSACTION en Cusco

  FASE 2 - COMMIT / ROLLBACK:
    - Si ambos PREPARE OK  → abrir nueva conexión y COMMIT PREPARED
    - Si alguno falla      → abrir nueva conexión y ROLLBACK PREPARED

NOTA: COMMIT PREPARED y ROLLBACK PREPARED deben ejecutarse en una
      conexión con autocommit=True independiente, porque después de
      PREPARE TRANSACTION la sesión original queda sin transacción
      activa y psycopg2 no permite cambiar autocommit en ese estado.
============================================================
"""

import sys
import time
import psycopg2
from config import NODOS, MONTO_TRANSFERENCIA, configurar_logging

log = configurar_logging("transfer_banco")


# ─────────────────────────────────────────────────────────────
# Utilidades de conexión
# ─────────────────────────────────────────────────────────────

def conectar(nodo: str, autocommit: bool = False) -> psycopg2.extensions.connection:
    """Abre y devuelve una conexión al nodo indicado."""
    params = NODOS[nodo]
    conn = psycopg2.connect(**params)
    conn.autocommit = autocommit
    log.info(f"Conexión establecida con nodo '{nodo}' "
             f"({params['host']}:{params['port']})")
    return conn


def obtener_saldo(conn, nodo: str) -> float:
    """Lee el saldo actual del nodo (primera cuenta de la tabla)."""
    with conn.cursor() as cur:
        cur.execute("SELECT saldo FROM cuentas LIMIT 1;")
        row = cur.fetchone()
        if row is None:
            raise RuntimeError(f"No se encontraron cuentas en el nodo '{nodo}'")
        return float(row[0])


def ejecutar_prepared(nodo: str, gid: str, accion: str) -> None:
    """
    Abre una conexión NUEVA con autocommit=True y ejecuta
    COMMIT PREPARED o ROLLBACK PREPARED para el GID dado.
    Usar siempre una conexión fresca para operaciones PREPARED.
    """
    conn = psycopg2.connect(**NODOS[nodo])
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f"{accion} PREPARED %s;", (gid,))
        log.info(f"[{nodo}] {accion} PREPARED '{gid}' ✓")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# Verificación de consistencia global
# ─────────────────────────────────────────────────────────────

def verificar_consistencia(suma_esperada: float) -> bool:
    """
    Abre conexiones frescas a los tres nodos y verifica que
    la suma de saldos se mantiene constante.
    """
    saldos = {}
    for nombre in ("arequipa", "cusco", "trujillo"):
        conn = psycopg2.connect(**NODOS[nombre])
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT saldo FROM cuentas LIMIT 1;")
            saldos[nombre] = float(cur.fetchone()[0])
        conn.close()

    suma_actual = sum(saldos.values())
    log.info("─── Verificación de consistencia global ───────────────")
    for nombre, saldo in saldos.items():
        log.info(f"  {nombre:>9} : S/ {saldo:>12,.2f}")
    log.info(f"  {'TOTAL':>9} : S/ {suma_actual:>12,.2f}  "
             f"(esperado: S/ {suma_esperada:,.2f})")
    log.info("───────────────────────────────────────────────────────")

    if abs(suma_actual - suma_esperada) < 0.01:
        log.info("✅ Consistencia global PRESERVADA.")
        return True
    else:
        log.error("❌ Inconsistencia detectada: la suma de saldos no coincide.")
        return False


# ─────────────────────────────────────────────────────────────
# Limpieza de transacciones huérfanas
# ─────────────────────────────────────────────────────────────

def limpiar_transacciones_huerfanas(nodo: str) -> None:
    """
    Revisa pg_prepared_xacts y hace ROLLBACK PREPARED sobre
    cualquier transacción pendiente. Usa conexión con autocommit=True.
    """
    conn = psycopg2.connect(**NODOS[nodo])
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT gid FROM pg_prepared_xacts "
                "WHERE database = current_database();"
            )
            pendientes = cur.fetchall()

        if pendientes:
            log.warning(f"[{nodo}] {len(pendientes)} transacción(es) huérfana(s). "
                        "Limpiando...")
            for (gid,) in pendientes:
                with conn.cursor() as cur:
                    cur.execute("ROLLBACK PREPARED %s;", (gid,))
                log.warning(f"[{nodo}] ROLLBACK PREPARED '{gid}' ✓")
        else:
            log.info(f"[{nodo}] Sin transacciones huérfanas pendientes.")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# Coordinador 2PC
# ─────────────────────────────────────────────────────────────

def ejecutar_transferencia_2pc(monto: float = MONTO_TRANSFERENCIA) -> bool:
    """
    Orquesta la transferencia usando Two-Phase Commit.
    Devuelve True si la transferencia se completó con éxito.
    """
    timestamp = int(time.time())
    gid_aqp   = f"tx_arequipa_{timestamp}"
    gid_cus   = f"tx_cusco_{timestamp}"

    # Registra qué nodos llegaron a PREPARE para saber a quién revertir
    preparados: list[tuple[str, str]] = []   # (nodo, gid)

    conn_aqp = conn_cus = None

    try:
        # ── Conexiones (autocommit=False para controlar la transacción) ──
        log.info("=" * 60)
        log.info("  INICIO - Transferencia 2PC")
        log.info(f"  Origen : Arequipa  →  Destino: Cusco")
        log.info(f"  Monto  : S/ {monto:,.2f}")
        log.info("=" * 60)

        conn_aqp = conectar("arequipa", autocommit=False)
        conn_cus = conectar("cusco",    autocommit=False)

        # Trujillo solo se usa para consistencia, con conexión propia después
        conn_tru_check = conectar("trujillo", autocommit=True)

        # ── Limpieza preventiva ─────────────────────────────
        limpiar_transacciones_huerfanas("arequipa")
        limpiar_transacciones_huerfanas("cusco")

        # ── Suma total inicial ───────────────────────────────
        saldo_tru_inicial = obtener_saldo(conn_tru_check, "trujillo")
        conn_tru_check.close()

        saldo_aqp_inicial = obtener_saldo(conn_aqp, "arequipa")
        saldo_cus_inicial = obtener_saldo(conn_cus, "cusco")
        suma_inicial = saldo_aqp_inicial + saldo_cus_inicial + saldo_tru_inicial
        log.info(f"Suma total inicial: S/ {suma_inicial:,.2f}")

        # ══════════════════════════════════════════════════════
        # FASE 1: PREPARE
        # ══════════════════════════════════════════════════════
        log.info("")
        log.info("── FASE 1: PREPARE ─────────────────────────────────")

        # 1a. Verificar saldo en Arequipa
        log.info(f"[arequipa] Saldo actual: S/ {saldo_aqp_inicial:,.2f}")
        if saldo_aqp_inicial < monto:
            raise ValueError(
                f"Saldo insuficiente en Arequipa. "
                f"Disponible: S/ {saldo_aqp_inicial:,.2f}, "
                f"Requerido: S/ {monto:,.2f}"
            )
        log.info("[arequipa] Saldo suficiente ✓")

        # 1b. Débito en Arequipa
        with conn_aqp.cursor() as cur:
            cur.execute(
                "UPDATE cuentas SET saldo = saldo - %s WHERE id = 1;", (monto,)
            )
        log.info(f"[arequipa] UPDATE aplicado: -S/ {monto:,.2f}")

        # 1c. Crédito en Cusco
        with conn_cus.cursor() as cur:
            cur.execute(
                "UPDATE cuentas SET saldo = saldo + %s WHERE id = 1;", (monto,)
            )
        log.info(f"[cusco]    UPDATE aplicado: +S/ {monto:,.2f}")

        # 1d. PREPARE en Arequipa
        with conn_aqp.cursor() as cur:
            cur.execute(f"PREPARE TRANSACTION '{gid_aqp}';")
        preparados.append(("arequipa", gid_aqp))
        log.info(f"[arequipa] PREPARE TRANSACTION '{gid_aqp}' ✓")

        # 1e. PREPARE en Cusco
        with conn_cus.cursor() as cur:
            cur.execute(f"PREPARE TRANSACTION '{gid_cus}';")
        preparados.append(("cusco", gid_cus))
        log.info(f"[cusco]    PREPARE TRANSACTION '{gid_cus}' ✓")

        # ══════════════════════════════════════════════════════
        # FASE 2: COMMIT
        # Las conexiones originales quedan liberadas tras el PREPARE.
        # Se usan conexiones NUEVAS con autocommit=True.
        # ══════════════════════════════════════════════════════
        log.info("")
        log.info("── FASE 2: COMMIT ──────────────────────────────────")

        for nodo, gid in preparados:
            ejecutar_prepared(nodo, gid, "COMMIT")

        log.info("")
        log.info("✅ Transferencia completada exitosamente.")
        log.info("")

        # ── Verificación de consistencia global ─────────────
        verificar_consistencia(suma_inicial)
        return True

    except Exception as exc:
        # ══════════════════════════════════════════════════════
        # FASE 2 (error): ROLLBACK de los que se prepararon
        # ══════════════════════════════════════════════════════
        log.error(f"Error durante el 2PC: {exc}")
        log.warning("── FASE 2 (ROLLBACK) ───────────────────────────────")

        for nodo, gid in preparados:
            try:
                ejecutar_prepared(nodo, gid, "ROLLBACK")
            except Exception as rb_exc:
                log.error(f"[{nodo}] Error al hacer ROLLBACK PREPARED: {rb_exc}")

        # Rollback de conexiones que NO llegaron al PREPARE (UPDATE sin preparar)
        for conn, label in [(conn_aqp, "arequipa"), (conn_cus, "cusco")]:
            nodo_ya_preparado = any(n == label for n, _ in preparados)
            if conn and not conn.closed and not nodo_ya_preparado:
                try:
                    conn.rollback()
                    log.warning(f"[{label}] ROLLBACK ejecutado (pre-PREPARE) ✓")
                except Exception:
                    pass

        log.error("❌ Transferencia REVERTIDA. Los saldos permanecen sin cambios.")
        return False

    finally:
        for conn in [conn_aqp, conn_cus]:
            if conn and not conn.closed:
                try:
                    conn.close()
                except Exception:
                    pass
        log.info("Conexiones cerradas.")


# ─────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    exito = ejecutar_transferencia_2pc()
    sys.exit(0 if exito else 1)
