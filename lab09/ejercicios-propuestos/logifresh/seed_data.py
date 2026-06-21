"""
Script para poblar el servicio de Inventario con productos de prueba.
Ejecutar DESPUÉS de levantar docker-compose (cuando todos los servicios están arriba):

    python seed_data.py

Requiere: pip install httpx
"""
import httpx

INVENTARIO_URL = "http://localhost:8001"

PRODUCTOS = [
    {"sku": "LCH-001", "nombre": "Leche Fresca Entera 1L", "categoria": "lacteos",
     "precio_unitario": 5.50, "stock_disponible": 200, "requiere_refrigeracion": True},
    {"sku": "YOG-002", "nombre": "Yogurt Natural 1L", "categoria": "lacteos",
     "precio_unitario": 8.90, "stock_disponible": 150, "requiere_refrigeracion": True},
    {"sku": "POL-003", "nombre": "Pollo Entero Refrigerado (kg)", "categoria": "carnes",
     "precio_unitario": 14.90, "stock_disponible": 80, "requiere_refrigeracion": True},
    {"sku": "QUE-004", "nombre": "Queso Fresco Paria (kg)", "categoria": "lacteos",
     "precio_unitario": 22.00, "stock_disponible": 60, "requiere_refrigeracion": True},
    {"sku": "VEG-005", "nombre": "Mix de Vegetales Congelados 500g", "categoria": "congelados",
     "precio_unitario": 9.50, "stock_disponible": 5, "requiere_refrigeracion": True},  # stock bajo a propósito
    {"sku": "ARR-006", "nombre": "Arroz Extra 5kg", "categoria": "abarrotes",
     "precio_unitario": 18.50, "stock_disponible": 300, "requiere_refrigeracion": False},
    {"sku": "ACE-007", "nombre": "Aceite Vegetal 1L", "categoria": "abarrotes",
     "precio_unitario": 11.20, "stock_disponible": 250, "requiere_refrigeracion": False},
    {"sku": "HEL-008", "nombre": "Helado Crema 1L", "categoria": "congelados",
     "precio_unitario": 16.00, "stock_disponible": 0, "requiere_refrigeracion": True},  # sin stock a propósito
]


def main():
    creados, existentes = 0, 0
    with httpx.Client(timeout=10.0) as client:
        for p in PRODUCTOS:
            r = client.post(f"{INVENTARIO_URL}/productos", json=p)
            if r.status_code == 201:
                creados += 1
                print(f"  ✓ Creado: {p['sku']} - {p['nombre']}")
            elif r.status_code == 409:
                existentes += 1
                print(f"  · Ya existía: {p['sku']}")
            else:
                print(f"  ✗ Error con {p['sku']}: {r.status_code} {r.text}")

    print(f"\nResumen: {creados} productos creados, {existentes} ya existentes.")


if __name__ == "__main__":
    main()
