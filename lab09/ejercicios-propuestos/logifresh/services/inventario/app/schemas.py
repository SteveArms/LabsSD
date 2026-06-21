from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductoCreate(BaseModel):
    sku: str
    nombre: str
    categoria: str = "general"
    precio_unitario: float
    stock_disponible: int = 0
    requiere_refrigeracion: bool = False


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    precio_unitario: Optional[float] = None
    stock_disponible: Optional[int] = None
    requiere_refrigeracion: Optional[bool] = None


class ProductoOut(BaseModel):
    id: int
    sku: str
    nombre: str
    categoria: str
    precio_unitario: float
    stock_disponible: int
    stock_reservado: int
    requiere_refrigeracion: bool

    class Config:
        from_attributes = True


class ReservaRequest(BaseModel):
    sku: str
    cantidad: int
    pedido_id: int


class ReservaResponse(BaseModel):
    sku: str
    cantidad_solicitada: int
    reservado: bool
    stock_disponible_restante: int
    mensaje: str


class ConfirmarRequest(BaseModel):
    sku: str
    cantidad: int
    pedido_id: int


class LiberarRequest(BaseModel):
    sku: str
    cantidad: int
    pedido_id: int
