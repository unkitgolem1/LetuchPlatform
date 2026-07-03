from pydantic import BaseModel, BeforeValidator
from typing import Annotated
from decimal import Decimal
from typing import Optional
from datetime import datetime


def _str(v):
    return str(v) if not isinstance(v, str) else v


UUIDStr = Annotated[str, BeforeValidator(_str)]


class User(BaseModel):
    """Usuario público — sin password. Úsalo en respuestas y templates."""
    id_usuario: UUIDStr
    id_sesion: UUIDStr
    nombre: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = ""
    created_at: Optional[datetime] = None

    @property
    def miembros_desde(self) -> Optional[str]:
        """Alias para el template perfil.html."""
        if self.created_at:
            return self.created_at.strftime("%d/%m/%Y")
        return None


class UserWithPsw(User):
    """Usuario completo con hash — solo para capa de repositorio."""
    password_hash: str


class Sesion(BaseModel):
    id: UUIDStr
    created_at: datetime
    expires_at: datetime


class CarritoItem(BaseModel):
    id_item: UUIDStr
    id_carrito: UUIDStr
    id_producto: int
    titulo: str
    descripcion: str = ""
    imagen: str = ""
    precio_unitario: Decimal
    cantidad: int
    subtotal: Decimal


class Carrito(BaseModel):
    id_carrito: UUIDStr
    id_sesion: UUIDStr
    estado: str = "activo"
    items: list[CarritoItem] = []

    @property
    def total(self) -> Decimal:
        return sum(i.subtotal for i in self.items)

    @property
    def cantidad_items(self) -> int:
        return sum(i.cantidad for i in self.items)


class PedidoItem(BaseModel):
    id_pedido_item: UUIDStr
    id_pedido: UUIDStr
    id_producto: int
    titulo: str
    precio_unitario: Decimal
    cantidad: int
    subtotal: Decimal
    imagen: str = ""
    created_at: Optional[datetime] = None


class Pedido(BaseModel):
    id_pedido: UUIDStr
    id_sesion: UUIDStr
    id_usuario: Optional[UUIDStr] = None
    estado: str = "pendiente"
    total: Decimal
    cantidad_items: int = 0
    cantidad_productos: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[PedidoItem] = []

    @property
    def fecha(self) -> Optional[str]:
        if self.created_at:
            return self.created_at.strftime("%d/%m/%Y %H:%M")
        return None

    @property
    def estado_label(self) -> str:
        return {
            "pendiente": "Pendiente",
            "confirmado": "Confirmado",
            "entregado": "Entregado",
            "cancelado": "Cancelado",
        }.get(self.estado, self.estado)
