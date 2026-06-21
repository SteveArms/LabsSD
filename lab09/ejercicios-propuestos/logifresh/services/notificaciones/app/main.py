import os
import time
import random
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db, Base

app = FastAPI(title="Servicio de Notificaciones - LogiFresh", version="1.0.0")

Base.metadata.create_all(bind=engine)

# Latencia simulada del proveedor de envío de correos/SMS (ms).
# Configurable por variable de entorno para usarse luego en las pruebas
# de rendimiento e integración (Actividad 3 y 4 de la guía).
DELAY_BASE_MS = float(os.getenv("NOTIFICACIONES_DELAY_MS", "200"))
DELAY_JITTER_MS = float(os.getenv("NOTIFICACIONES_DELAY_JITTER_MS", "150"))
TASA_FALLO = float(os.getenv("NOTIFICACIONES_TASA_FALLO", "0.0"))  # 0.0 a 1.0


@app.get("/health")
def health():
    return {"status": "ok", "service": "notificaciones"}


@app.post("/notificaciones", response_model=schemas.NotificacionOut, status_code=201)
def enviar_notificacion(datos: schemas.NotificacionCreate, db: Session = Depends(get_db)):
    inicio = time.perf_counter()

    delay_s = (DELAY_BASE_MS + random.uniform(0, DELAY_JITTER_MS)) / 1000.0
    time.sleep(delay_s)

    fallo = random.random() < TASA_FALLO
    estado = "FALLIDA" if fallo else "ENVIADA"

    tiempo_total_ms = (time.perf_counter() - inicio) * 1000.0

    notif = models.Notificacion(
        pedido_id=datos.pedido_id,
        destinatario=datos.destinatario,
        canal=datos.canal,
        tipo=datos.tipo,
        mensaje=datos.mensaje,
        estado=estado,
        tiempo_envio_ms=round(tiempo_total_ms, 2),
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


@app.get("/notificaciones", response_model=List[schemas.NotificacionOut])
def listar_notificaciones(pedido_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.Notificacion)
    if pedido_id is not None:
        q = q.filter(models.Notificacion.pedido_id == pedido_id)
    return q.order_by(models.Notificacion.id.desc()).limit(200).all()
