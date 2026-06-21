from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from .database import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, nullable=True, index=True)
    destinatario = Column(String, nullable=False)
    canal = Column(String, default="EMAIL")  # EMAIL, SMS
    tipo = Column(String, nullable=False)  # CONFIRMACION_PEDIDO, FACTURA_EMITIDA, ENVIO_PROGRAMADO, etc.
    mensaje = Column(String, nullable=False)
    estado = Column(String, default="PENDIENTE")  # PENDIENTE, ENVIADA, FALLIDA
    tiempo_envio_ms = Column(Float, default=0.0)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
