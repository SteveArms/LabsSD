"""
config.py
============================================================
Configuración centralizada de conexiones a los tres nodos
PostgreSQL del Sistema Nacional de Bancos Cooperativos.

Todos los parámetros se leen desde el archivo .env ubicado
en la raíz del proyecto.
============================================================
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Cargar variables de entorno ──────────────────────────────
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# ── Parámetros de conexión por nodo ─────────────────────────
NODOS: dict[str, dict] = {
    "arequipa": {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("PORT_AREQUIPA", "5433")),
        "dbname":   os.getenv("DB_NAME_AREQUIPA", "banco_arequipa"),
        "user":     os.getenv("DB_USER", "admin"),
        "password": os.getenv("DB_PASSWORD", "admin123"),
        "connect_timeout": 5,
    },
    "cusco": {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("PORT_CUSCO", "5434")),
        "dbname":   os.getenv("DB_NAME_CUSCO", "banco_cusco"),
        "user":     os.getenv("DB_USER", "admin"),
        "password": os.getenv("DB_PASSWORD", "admin123"),
        "connect_timeout": 5,
    },
    "trujillo": {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     int(os.getenv("PORT_TRUJILLO", "5435")),
        "dbname":   os.getenv("DB_NAME_TRUJILLO", "banco_trujillo"),
        "user":     os.getenv("DB_USER", "admin"),
        "password": os.getenv("DB_PASSWORD", "admin123"),
        "connect_timeout": 5,
    },
}

# ── Monto de la transferencia ────────────────────────────────
MONTO_TRANSFERENCIA: float = float(os.getenv("MONTO_TRANSFERENCIA", "25000"))


# ── Configuración de logging ─────────────────────────────────
def configurar_logging(nombre: str = "bancos_2pc") -> logging.Logger:
    """
    Devuelve un logger con formato estándar para todos los scripts.
    El nivel INFO muestra el flujo normal; WARNING y ERROR señalan
    situaciones anómalas o fallos.
    """
    logger = logging.getLogger(nombre)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)-8s] %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
