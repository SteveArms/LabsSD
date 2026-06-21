from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from . import models, schemas
from .database import engine, get_db, Base

app = FastAPI(title="Servicio de Inventario - LogiFresh", version="1.0.0")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "inventario"}


@app.post("/productos", response_model=schemas.ProductoOut, status_code=201)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Producto).filter(models.Producto.sku == producto.sku).first()
    if existente:
        raise HTTPException(status_code=409, detail="El SKU ya existe")
    nuevo = models.Producto(
        sku=producto.sku,
        nombre=producto.nombre,
        categoria=producto.categoria,
        precio_unitario=producto.precio_unitario,
        stock_disponible=producto.stock_disponible,
        requiere_refrigeracion=int(producto.requiere_refrigeracion),
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _to_out(nuevo)


@app.get("/productos", response_model=List[schemas.ProductoOut])
def listar_productos(db: Session = Depends(get_db)):
    productos = db.query(models.Producto).all()
    return [_to_out(p) for p in productos]


@app.get("/productos/{sku}", response_model=schemas.ProductoOut)
def obtener_producto(sku: str, db: Session = Depends(get_db)):
    p = db.query(models.Producto).filter(models.Producto.sku == sku).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _to_out(p)


@app.patch("/productos/{sku}", response_model=schemas.ProductoOut)
def actualizar_producto(sku: str, datos: schemas.ProductoUpdate, db: Session = Depends(get_db)):
    p = db.query(models.Producto).filter(models.Producto.sku == sku).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if datos.nombre is not None:
        p.nombre = datos.nombre
    if datos.precio_unitario is not None:
        p.precio_unitario = datos.precio_unitario
    if datos.stock_disponible is not None:
        p.stock_disponible = datos.stock_disponible
    if datos.requiere_refrigeracion is not None:
        p.requiere_refrigeracion = int(datos.requiere_refrigeracion)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@app.post("/inventario/reservar", response_model=schemas.ReservaResponse)
def reservar_stock(req: schemas.ReservaRequest, db: Session = Depends(get_db)):
    """Reserva stock para un pedido. No descuenta el stock hasta confirmar."""
    p = db.query(models.Producto).filter(models.Producto.sku == req.sku).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Producto {req.sku} no encontrado")

    if p.stock_disponible < req.cantidad:
        return schemas.ReservaResponse(
            sku=req.sku,
            cantidad_solicitada=req.cantidad,
            reservado=False,
            stock_disponible_restante=p.stock_disponible,
            mensaje="Stock insuficiente",
        )

    p.stock_disponible -= req.cantidad
    p.stock_reservado += req.cantidad
    db.add(models.MovimientoInventario(
        sku=req.sku, tipo="RESERVA", cantidad=req.cantidad, pedido_id=req.pedido_id
    ))
    db.commit()
    db.refresh(p)
    return schemas.ReservaResponse(
        sku=req.sku,
        cantidad_solicitada=req.cantidad,
        reservado=True,
        stock_disponible_restante=p.stock_disponible,
        mensaje="Stock reservado correctamente",
    )


@app.post("/inventario/confirmar")
def confirmar_reserva(req: schemas.ConfirmarRequest, db: Session = Depends(get_db)):
    """Confirma una reserva ya hecha (descuenta definitivamente del stock reservado)."""
    p = db.query(models.Producto).filter(models.Producto.sku == req.sku).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if p.stock_reservado < req.cantidad:
        raise HTTPException(status_code=400, detail="No existe reserva suficiente para confirmar")
    p.stock_reservado -= req.cantidad
    db.add(models.MovimientoInventario(
        sku=req.sku, tipo="CONFIRMACION", cantidad=req.cantidad, pedido_id=req.pedido_id
    ))
    db.commit()
    return {"mensaje": "Reserva confirmada", "sku": req.sku, "cantidad": req.cantidad}


@app.post("/inventario/liberar")
def liberar_reserva(req: schemas.LiberarRequest, db: Session = Depends(get_db)):
    """Libera una reserva (por ejemplo al cancelar un pedido) y regresa el stock a disponible."""
    p = db.query(models.Producto).filter(models.Producto.sku == req.sku).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    cantidad_a_liberar = min(req.cantidad, p.stock_reservado)
    p.stock_reservado -= cantidad_a_liberar
    p.stock_disponible += cantidad_a_liberar
    db.add(models.MovimientoInventario(
        sku=req.sku, tipo="LIBERACION", cantidad=cantidad_a_liberar, pedido_id=req.pedido_id
    ))
    db.commit()
    return {"mensaje": "Reserva liberada", "sku": req.sku, "cantidad_liberada": cantidad_a_liberar}


@app.get("/inventario/movimientos")
def listar_movimientos(sku: str = None, db: Session = Depends(get_db)):
    q = db.query(models.MovimientoInventario)
    if sku:
        q = q.filter(models.MovimientoInventario.sku == sku)
    return q.order_by(models.MovimientoInventario.id.desc()).limit(200).all()


def _to_out(p: models.Producto) -> schemas.ProductoOut:
    return schemas.ProductoOut(
        id=p.id,
        sku=p.sku,
        nombre=p.nombre,
        categoria=p.categoria,
        precio_unitario=p.precio_unitario,
        stock_disponible=p.stock_disponible,
        stock_reservado=p.stock_reservado,
        requiere_refrigeracion=bool(p.requiere_refrigeracion),
    )
