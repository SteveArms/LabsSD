from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from . import models, schemas
from .database import engine, get_db, Base

app = FastAPI(title="Servicio de Facturación - LogiFresh", version="1.0.0")

Base.metadata.create_all(bind=engine)

# Catálogo simple de promociones válidas (código -> % descuento)
PROMOCIONES = {
    "LOGIFRESH10": 10.0,
    "LOGIFRESH20": 20.0,
    "BIENVENIDA5": 5.0,
}


@app.get("/health")
def health():
    return {"status": "ok", "service": "facturacion"}


@app.post("/facturas", response_model=schemas.FacturaOut, status_code=201)
def emitir_factura(datos: schemas.FacturaCreate, db: Session = Depends(get_db)):
    # Idempotencia: si ya existe una factura para este pedido, se devuelve la existente
    # en lugar de crear una duplicada (evita el bug de "facturas duplicadas").
    existente = db.query(models.Factura).filter(models.Factura.pedido_id == datos.pedido_id).first()
    if existente:
        return _to_out(existente, db)

    subtotal = sum(item.cantidad * item.precio_unitario for item in datos.items)

    porcentaje_descuento = datos.porcentaje_descuento
    if datos.codigo_promocion:
        porcentaje_descuento = PROMOCIONES.get(datos.codigo_promocion, 0.0)

    descuento = round(subtotal * (porcentaje_descuento / 100.0), 2)
    total = round(subtotal - descuento, 2)

    factura = models.Factura(
        pedido_id=datos.pedido_id,
        cliente=datos.cliente,
        subtotal=subtotal,
        descuento=descuento,
        total=total,
        estado="EMITIDA",
    )
    db.add(factura)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existente = db.query(models.Factura).filter(models.Factura.pedido_id == datos.pedido_id).first()
        return _to_out(existente, db)

    db.refresh(factura)

    for item in datos.items:
        db.add(models.DetalleFactura(
            factura_id=factura.id,
            sku=item.sku,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            subtotal_item=round(item.cantidad * item.precio_unitario, 2),
        ))
    db.commit()

    return _to_out(factura, db)


@app.get("/facturas", response_model=List[schemas.FacturaOut])
def listar_facturas(db: Session = Depends(get_db)):
    facturas = db.query(models.Factura).all()
    return [_to_out(f, db) for f in facturas]


@app.get("/facturas/{factura_id}", response_model=schemas.FacturaOut)
def obtener_factura(factura_id: int, db: Session = Depends(get_db)):
    f = db.query(models.Factura).filter(models.Factura.id == factura_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return _to_out(f, db)


@app.get("/facturas/pedido/{pedido_id}", response_model=schemas.FacturaOut)
def obtener_factura_por_pedido(pedido_id: int, db: Session = Depends(get_db)):
    f = db.query(models.Factura).filter(models.Factura.pedido_id == pedido_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="No existe factura para ese pedido")
    return _to_out(f, db)


@app.post("/facturas/{factura_id}/anular")
def anular_factura(factura_id: int, db: Session = Depends(get_db)):
    f = db.query(models.Factura).filter(models.Factura.id == factura_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    f.estado = "ANULADA"
    db.commit()
    return {"mensaje": "Factura anulada", "factura_id": factura_id}


def _to_out(f: models.Factura, db: Session) -> schemas.FacturaOut:
    detalles = db.query(models.DetalleFactura).filter(models.DetalleFactura.factura_id == f.id).all()
    return schemas.FacturaOut(
        id=f.id,
        pedido_id=f.pedido_id,
        cliente=f.cliente,
        subtotal=f.subtotal,
        descuento=f.descuento,
        total=f.total,
        estado=f.estado,
        detalles=[schemas.DetalleOut.model_validate(d) for d in detalles],
    )
