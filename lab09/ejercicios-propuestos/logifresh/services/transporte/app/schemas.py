from pydantic import BaseModel
from typing import Optional


class EnvioCreate(BaseModel):
    pedido_id: int
    direccion_destino: str
    ciudad: str
    requiere_refrigeracion: bool = False


class EnvioUpdate(BaseModel):
    estado: Optional[str] = None
    transportista: Optional[str] = None


class EnvioOut(BaseModel):
    id: int
    pedido_id: int
    direccion_destino: str
    ciudad: str
    requiere_refrigeracion: bool
    transportista: str
    estado: str
    costo_envio: float

    class Config:
        from_attributes = True
