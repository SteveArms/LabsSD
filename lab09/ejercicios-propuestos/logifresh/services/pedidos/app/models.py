from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String, nullable=False)
    direccion_entrega = Column(String, nullable=False)
    ciudad = Column(String, nullable=False)
    codigo_promocion = Column(String, nullable=True)
    subtotal = Column(Float, default=0.0)
    descuento = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    estado = Column(String, default="PENDIENTE")
    # PENDIENTE, CONFIRMADO, RECHAZADO_SIN_STOCK, CANCELADO, ERROR_PROCESAMIENTO
    factura_id = Column(Integer, nullable=True)
    envio_id = Column(Integer, nullable=True)
    detalle_error = Column(String, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, nullable=False, index=True)
    sku = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
