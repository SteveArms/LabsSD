import os
import httpx

INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://inventario:8000")
FACTURACION_URL = os.getenv("FACTURACION_URL", "http://facturacion:8000")
TRANSPORTE_URL = os.getenv("TRANSPORTE_URL", "http://transporte:8000")
NOTIFICACIONES_URL = os.getenv("NOTIFICACIONES_URL", "http://notificaciones:8000")

TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def obtener_producto(sku: str):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.get(f"{INVENTARIO_URL}/productos/{sku}")
    r.raise_for_status()
    return r.json()


def reservar_stock(sku: str, cantidad: int, pedido_id: int):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{INVENTARIO_URL}/inventario/reservar", json={
            "sku": sku, "cantidad": cantidad, "pedido_id": pedido_id
        })
    r.raise_for_status()
    return r.json()


def confirmar_stock(sku: str, cantidad: int, pedido_id: int):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{INVENTARIO_URL}/inventario/confirmar", json={
            "sku": sku, "cantidad": cantidad, "pedido_id": pedido_id
        })
    r.raise_for_status()
    return r.json()


def liberar_stock(sku: str, cantidad: int, pedido_id: int):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{INVENTARIO_URL}/inventario/liberar", json={
            "sku": sku, "cantidad": cantidad, "pedido_id": pedido_id
        })
    r.raise_for_status()
    return r.json()


def emitir_factura(pedido_id: int, cliente: str, items: list, porcentaje_descuento: float, codigo_promocion: str = None):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{FACTURACION_URL}/facturas", json={
            "pedido_id": pedido_id,
            "cliente": cliente,
            "items": items,
            "porcentaje_descuento": porcentaje_descuento,
            "codigo_promocion": codigo_promocion,
        })
    r.raise_for_status()
    return r.json()


def anular_factura(factura_id: int):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{FACTURACION_URL}/facturas/{factura_id}/anular")
    r.raise_for_status()
    return r.json()


def programar_envio(pedido_id: int, direccion_destino: str, ciudad: str, requiere_refrigeracion: bool):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{TRANSPORTE_URL}/envios", json={
            "pedido_id": pedido_id,
            "direccion_destino": direccion_destino,
            "ciudad": ciudad,
            "requiere_refrigeracion": requiere_refrigeracion,
        })
    r.raise_for_status()
    return r.json()


def cancelar_envio(envio_id: int):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.patch(f"{TRANSPORTE_URL}/envios/{envio_id}", json={"estado": "CANCELADO"})
    r.raise_for_status()
    return r.json()


def enviar_notificacion(pedido_id: int, destinatario: str, tipo: str, mensaje: str, canal: str = "EMAIL"):
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(f"{NOTIFICACIONES_URL}/notificaciones", json={
            "pedido_id": pedido_id,
            "destinatario": destinatario,
            "canal": canal,
            "tipo": tipo,
            "mensaje": mensaje,
        })
    r.raise_for_status()
    return r.json()
