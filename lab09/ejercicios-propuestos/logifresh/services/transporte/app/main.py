import random
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db, Base

app = FastAPI(title="Servicio de Transporte - LogiFresh", version="1.0.0")

Base.metadata.create_all(bind=engine)

TRANSPORTISTAS = ["Transportes Andinos", "FrioExpress", "Rutas del Sur"]
COSTO_BASE = 15.0
COSTO_REFRIGERADO_EXTRA = 10.0


@app.get("/health")
def health():
    return {"status": "ok", "service": "transporte"}


@app.post("/envios", response_model=schemas.EnvioOut, status_code=201)
def programar_envio(datos: schemas.EnvioCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Envio).filter(models.Envio.pedido_id == datos.pedido_id).first()
    if existente:
        return existente

    costo = COSTO_BASE + (COSTO_REFRIGERADO_EXTRA if datos.requiere_refrigeracion else 0.0)

    envio = models.Envio(
        pedido_id=datos.pedido_id,
        direccion_destino=datos.direccion_destino,
        ciudad=datos.ciudad,
        requiere_refrigeracion=int(datos.requiere_refrigeracion),
        transportista=random.choice(TRANSPORTISTAS),
        estado="PROGRAMADO",
        costo_envio=costo,
    )
    db.add(envio)
    db.commit()
    db.refresh(envio)
    return _to_out(envio)


@app.get("/envios", response_model=List[schemas.EnvioOut])
def listar_envios(db: Session = Depends(get_db)):
    return [_to_out(e) for e in db.query(models.Envio).all()]


@app.get("/envios/pedido/{pedido_id}", response_model=schemas.EnvioOut)
def obtener_envio_por_pedido(pedido_id: int, db: Session = Depends(get_db)):
    e = db.query(models.Envio).filter(models.Envio.pedido_id == pedido_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="No existe envío para ese pedido")
    return _to_out(e)


@app.patch("/envios/{envio_id}", response_model=schemas.EnvioOut)
def actualizar_envio(envio_id: int, datos: schemas.EnvioUpdate, db: Session = Depends(get_db)):
    e = db.query(models.Envio).filter(models.Envio.id == envio_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Envío no encontrado")
    if datos.estado is not None:
        e.estado = datos.estado
    if datos.transportista is not None:
        e.transportista = datos.transportista
    db.commit()
    db.refresh(e)
    return _to_out(e)


def _to_out(e: models.Envio) -> schemas.EnvioOut:
    return schemas.EnvioOut(
        id=e.id,
        pedido_id=e.pedido_id,
        direccion_destino=e.direccion_destino,
        ciudad=e.ciudad,
        requiere_refrigeracion=bool(e.requiere_refrigeracion),
        transportista=e.transportista,
        estado=e.estado,
        costo_envio=e.costo_envio,
    )
