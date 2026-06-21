from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from .database import Base


class Envio(Base):
    __tablename__ = "envios"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, nullable=False, index=True)
    direccion_destino = Column(String, nullable=False)
    ciudad = Column(String, nullable=False)
    requiere_refrigeracion = Column(Integer, default=0)
    transportista = Column(String, default="Sin asignar")
    estado = Column(String, default="PROGRAMADO")  # PROGRAMADO, EN_RUTA, ENTREGADO, FALLIDO
    costo_envio = Column(Float, default=0.0)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
