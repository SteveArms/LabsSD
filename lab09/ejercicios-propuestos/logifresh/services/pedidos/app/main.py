import httpx
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, clients
from .database import engine, get_db, Base

app = FastAPI(title="Servicio de Pedidos - LogiFresh", version="1.0.0")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "pedidos"}


@app.post("/pedidos", response_model=schemas.PedidoOut, status_code=201)
def crear_pedido(datos: schemas.PedidoCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not datos.items:
        raise HTTPException(status_code=400, detail="El pedido debe tener al menos un ítem")

    # 1. Crear registro de pedido en estado PENDIENTE
    pedido = models.Pedido(
        cliente=datos.cliente,
        direccion_entrega=datos.direccion_entrega,
        ciudad=datos.ciudad,
        codigo_promocion=datos.codigo_promocion,
        estado="PENDIENTE",
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    reservas_realizadas = []  # para poder revertir si algo falla
    items_con_precio = []
    requiere_refrigeracion = False

    try:
        # 2. Verificar producto + reservar stock para cada ítem
        for item in datos.items:
            try:
                producto = clients.obtener_producto(item.sku)
            except httpx.HTTPStatusError:
                raise PedidoFallido(f"El producto {item.sku} no existe en inventario")
            except httpx.RequestError:
                raise PedidoFallido("No se pudo contactar al servicio de Inventario")

            if producto.get("requiere_refrigeracion"):
                requiere_refrigeracion = True

            reserva = clients.reservar_stock(item.sku, item.cantidad, pedido.id)
            if not reserva.get("reservado"):
                raise PedidoFallido(
                    f"Stock insuficiente para {item.sku} (disponible: {reserva.get('stock_disponible_restante')})",
                    estado="RECHAZADO_SIN_STOCK",
                )
            reservas_realizadas.append((item.sku, item.cantidad))

            items_con_precio.append({
                "sku": item.sku,
                "cantidad": item.cantidad,
                "precio_unitario": producto["precio_unitario"],
            })

        # 3. Confirmar todas las reservas (descuento definitivo del stock)
        for sku, cantidad in reservas_realizadas:
            clients.confirmar_stock(sku, cantidad, pedido.id)

        subtotal = sum(i["cantidad"] * i["precio_unitario"] for i in items_con_precio)

        # 4. Emitir factura (idempotente por pedido_id en el servicio de Facturación)
        try:
            factura = clients.emitir_factura(
                pedido_id=pedido.id,
                cliente=datos.cliente,
                items=items_con_precio,
                porcentaje_descuento=0.0,
                codigo_promocion=datos.codigo_promocion,
            )
        except httpx.RequestError:
            raise PedidoFallido("No se pudo contactar al servicio de Facturación")

        # 5. Programar el envío
        try:
            envio = clients.programar_envio(
                pedido_id=pedido.id,
                direccion_destino=datos.direccion_entrega,
                ciudad=datos.ciudad,
                requiere_refrigeracion=requiere_refrigeracion,
            )
        except httpx.RequestError:
            raise PedidoFallido("No se pudo contactar al servicio de Transporte")

        # 6. Guardar detalle y actualizar estado del pedido
        for i in items_con_precio:
            db.add(models.DetallePedido(
                pedido_id=pedido.id, sku=i["sku"], cantidad=i["cantidad"], precio_unitario=i["precio_unitario"]
            ))

        pedido.subtotal = factura["subtotal"]
        pedido.descuento = factura["descuento"]
        pedido.total = factura["total"]
        pedido.estado = "CONFIRMADO"
        pedido.factura_id = factura["id"]
        pedido.envio_id = envio["id"]
        db.commit()
        db.refresh(pedido)

        # 7. Notificar al cliente (se ejecuta en segundo plano, no bloquea la respuesta)
        background_tasks.add_task(
            clients.enviar_notificacion,
            pedido.id,
            datos.cliente,
            "CONFIRMACION_PEDIDO",
            f"Su pedido #{pedido.id} fue confirmado. Total a pagar: S/ {pedido.total:.2f}",
        )

        return _to_out(pedido, db)

    except PedidoFallido as e:
        # Revertir reservas de inventario ya realizadas
        for sku, cantidad in reservas_realizadas:
            try:
                clients.liberar_stock(sku, cantidad, pedido.id)
            except httpx.RequestError:
                pass
        pedido.estado = e.estado
        pedido.detalle_error = e.mensaje
        db.commit()
        db.refresh(pedido)
        raise HTTPException(status_code=e.http_status, detail=e.mensaje)


class PedidoFallido(Exception):
    def __init__(self, mensaje: str, estado: str = "ERROR_PROCESAMIENTO", http_status: int = 422):
        self.mensaje = mensaje
        self.estado = estado
        self.http_status = http_status
        super().__init__(mensaje)


@app.get("/pedidos", response_model=List[schemas.PedidoOut])
def listar_pedidos(db: Session = Depends(get_db)):
    pedidos = db.query(models.Pedido).all()
    return [_to_out(p, db) for p in pedidos]


@app.get("/pedidos/{pedido_id}", response_model=schemas.PedidoOut)
def obtener_pedido(pedido_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return _to_out(p, db)


@app.post("/pedidos/{pedido_id}/cancelar", response_model=schemas.PedidoOut)
def cancelar_pedido(pedido_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    p = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if p.estado not in ("CONFIRMADO", "PENDIENTE"):
        raise HTTPException(status_code=400, detail=f"No se puede cancelar un pedido en estado {p.estado}")

    detalles = db.query(models.DetallePedido).filter(models.DetallePedido.pedido_id == pedido_id).all()
    for d in detalles:
        try:
            clients.liberar_stock(d.sku, d.cantidad, pedido_id)
        except httpx.RequestError:
            pass

    if p.factura_id:
        try:
            clients.anular_factura(p.factura_id)
        except httpx.RequestError:
            pass

    if p.envio_id:
        try:
            clients.cancelar_envio(p.envio_id)
        except httpx.RequestError:
            pass

    p.estado = "CANCELADO"
    db.commit()
    db.refresh(p)

    background_tasks.add_task(
        clients.enviar_notificacion,
        p.id,
        p.cliente,
        "CANCELACION_PEDIDO",
        f"Su pedido #{p.id} fue cancelado.",
    )

    return _to_out(p, db)


def _to_out(p: models.Pedido, db: Session) -> schemas.PedidoOut:
    items = db.query(models.DetallePedido).filter(models.DetallePedido.pedido_id == p.id).all()
    return schemas.PedidoOut(
        id=p.id,
        cliente=p.cliente,
        direccion_entrega=p.direccion_entrega,
        ciudad=p.ciudad,
        codigo_promocion=p.codigo_promocion,
        subtotal=p.subtotal,
        descuento=p.descuento,
        total=p.total,
        estado=p.estado,
        factura_id=p.factura_id,
        envio_id=p.envio_id,
        detalle_error=p.detalle_error,
        items=[schemas.DetalleOut.model_validate(i) for i in items],
    )
