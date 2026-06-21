from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    categoria = Column(String, default="general")
    precio_unitario = Column(Float, nullable=False)
    stock_disponible = Column(Integer, nullable=False, default=0)
    stock_reservado = Column(Integer, nullable=False, default=0)
    requiere_refrigeracion = Column(Integer, default=0)  # 0/1 boolean
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, index=True, nullable=False)
    tipo = Column(String, nullable=False)  # RESERVA, CONFIRMACION, LIBERACION, REPOSICION
    cantidad = Column(Integer, nullable=False)
    pedido_id = Column(Integer, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
