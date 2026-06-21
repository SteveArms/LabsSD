from pydantic import BaseModel
from typing import Optional


class NotificacionCreate(BaseModel):
    pedido_id: Optional[int] = None
    destinatario: str
    canal: str = "EMAIL"
    tipo: str
    mensaje: str


class NotificacionOut(BaseModel):
    id: int
    pedido_id: Optional[int]
    destinatario: str
    canal: str
    tipo: str
    mensaje: str
    estado: str
    tiempo_envio_ms: float

    class Config:
        from_attributes = True
