import os
from dotenv import load_dotenv

load_dotenv()

ARQUIPA_CONFIG = {
    "dbname": os.getenv("ARQUIPA_DB", "almacen_arequipa"),
    "user": os.getenv("ARQUIPA_USER", "admin"),
    "password": os.getenv("ARQUIPA_PASSWORD", "secret"),
    "host": os.getenv("ARQUIPA_HOST", "localhost"),
    "port": int(os.getenv("ARQUIPA_PORT", 5433))
}

LIMA_CONFIG = {
    "dbname": os.getenv("LIMA_DB", "almacen_lima"),
    "user": os.getenv("LIMA_USER", "admin"),
    "password": os.getenv("LIMA_PASSWORD", "secret"),
    "host": os.getenv("LIMA_HOST", "localhost"),
    "port": int(os.getenv("LIMA_PORT", 5434))
}

PRODUCTO = os.getenv("PRODUCTO", "Paracetamol")
CANTIDAD = int(os.getenv("CANTIDAD", "20"))