from pydantic import BaseModel
from typing import List, Optional


class ItemPedido(BaseModel):
    sku: str
    cantidad: int


class PedidoCreate(BaseModel):
    cliente: str
    direccion_entrega: str
    ciudad: str
    items: List[ItemPedido]
    codigo_promocion: Optional[str] = None


class DetalleOut(BaseModel):
    sku: str
    cantidad: int
    precio_unitario: float

    class Config:
        from_attributes = True


class PedidoOut(BaseModel):
    id: int
    cliente: str
    direccion_entrega: str
    ciudad: str
    codigo_promocion: Optional[str]
    subtotal: float
    descuento: float
    total: float
    estado: str
    factura_id: Optional[int]
    envio_id: Optional[int]
    detalle_error: Optional[str]
    items: List[DetalleOut] = []

    class Config:
        from_attributes = True
