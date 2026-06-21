from pydantic import BaseModel
from typing import List, Optional


class ItemFactura(BaseModel):
    sku: str
    cantidad: int
    precio_unitario: float


class FacturaCreate(BaseModel):
    pedido_id: int
    cliente: str
    items: List[ItemFactura]
    porcentaje_descuento: float = 0.0  # 0 a 100
    codigo_promocion: Optional[str] = None


class DetalleOut(BaseModel):
    sku: str
    cantidad: int
    precio_unitario: float
    subtotal_item: float

    class Config:
        from_attributes = True


class FacturaOut(BaseModel):
    id: int
    pedido_id: int
    cliente: str
    subtotal: float
    descuento: float
    total: float
    estado: str
    detalles: List[DetalleOut] = []

    class Config:
        from_attributes = True
