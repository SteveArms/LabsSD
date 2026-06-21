from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from .database import Base


class Factura(Base):
    __tablename__ = "facturas"
    __table_args__ = (
        UniqueConstraint("pedido_id", name="uq_factura_pedido"),
    )

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, nullable=False, index=True)
    cliente = Column(String, nullable=False)
    subtotal = Column(Float, nullable=False)
    descuento = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False)
    estado = Column(String, default="EMITIDA")  # EMITIDA, ANULADA
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class DetalleFactura(Base):
    __tablename__ = "detalle_factura"

    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, nullable=False, index=True)
    sku = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal_item = Column(Float, nullable=False)
