"""Unit tests for models.py — Pydantic models."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from models import (
    User, UserWithPsw, Sesion,
    Carrito, CarritoItem,
    Pedido, PedidoItem,
    UUIDStr,
)
from auth import hash_password


class TestUser:
    def test_create_minimal(self):
        u = User(
            id_usuario="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            id_sesion="11111111-2222-3333-4444-555555555555",
        )
        assert u.nombre is None
        assert u.email is None
        assert u.avatar == ""

    def test_create_full(self):
        now = datetime.now(timezone.utc)
        u = User(
            id_usuario="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            id_sesion="11111111-2222-3333-4444-555555555555",
            nombre="Alice",
            email="alice@example.com",
            avatar="https://example.com/avatar.png",
            created_at=now,
        )
        assert u.nombre == "Alice"
        assert u.email == "alice@example.com"
        assert u.avatar == "https://example.com/avatar.png"

    def test_miembros_desde_property(self):
        u = User(
            id_usuario="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            id_sesion="11111111-2222-3333-4444-555555555555",
            created_at=datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc),
        )
        assert u.miembros_desde == "15/03/2024"

    def test_miembros_desde_none(self):
        u = User(
            id_usuario="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            id_sesion="11111111-2222-3333-4444-555555555555",
        )
        assert u.miembros_desde is None

    def test_uuid_str_converts_int(self):
        u = User(
            id_usuario=123456789012345678901234567890123456,
            id_sesion="11111111-2222-3333-4444-555555555555",
        )
        assert isinstance(u.id_usuario, str)


class TestUserWithPsw:
    def test_extends_user(self):
        u = UserWithPsw(
            id_usuario="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            id_sesion="11111111-2222-3333-4444-555555555555",
            password_hash=hash_password("secret"),
        )
        assert isinstance(u, User)
        assert u.password_hash

    def test_password_hash_accessible(self):
        h = hash_password("mypassword")
        u = UserWithPsw(
            id_usuario="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            id_sesion="11111111-2222-3333-4444-555555555555",
            password_hash=h,
        )
        assert u.password_hash == h


class TestSesion:
    def test_create(self):
        now = datetime.now(timezone.utc)
        s = Sesion(
            id="session-1111-2222-3333-444455556666",
            created_at=now,
            expires_at=now,
        )
        assert s.id == "session-1111-2222-3333-444455556666"
        assert s.created_at == now
        assert s.expires_at == now


class TestCarritoItem:
    def test_create(self):
        item = CarritoItem(
            id_item="item-0001-0000-0000-000000000001",
            id_carrito="cart-0001-0000-0000-000000000001",
            id_producto=1,
            titulo="Pan de Muerto",
            precio_unitario=Decimal("35.00"),
            cantidad=2,
            subtotal=Decimal("70.00"),
        )
        assert item.titulo == "Pan de Muerto"
        assert item.precio_unitario == Decimal("35.00")
        assert item.subtotal == Decimal("70.00")

    def test_defaults(self):
        item = CarritoItem(
            id_item="x", id_carrito="y", id_producto=1,
            titulo="T", precio_unitario=Decimal("1"),
            cantidad=1, subtotal=Decimal("1"),
        )
        assert item.descripcion == ""
        assert item.imagen == ""


class TestCarrito:
    def test_empty_cart_total(self):
        c = Carrito(
            id_carrito="c1", id_sesion="s1",
        )
        assert c.total == Decimal("0")
        assert c.cantidad_items == 0

    def test_cart_with_items(self):
        items = [
            CarritoItem(
                id_item=f"i{i}", id_carrito="c1", id_producto=i,
                titulo=f"Product {i}",
                precio_unitario=Decimal(str(10 * i)),
                cantidad=i,
                subtotal=Decimal(str(10 * i * i)),
            )
            for i in range(1, 4)
        ]
        c = Carrito(id_carrito="c1", id_sesion="s1", items=items)
        assert c.total == Decimal("10") + Decimal("40") + Decimal("90")
        assert c.cantidad_items == 1 + 2 + 3

    def test_cart_estado_default(self):
        c = Carrito(id_carrito="c1", id_sesion="s1")
        assert c.estado == "activo"


class TestPedidoItem:
    def test_create(self):
        item = PedidoItem(
            id_pedido_item="pi1", id_pedido="p1",
            id_producto=1, titulo="Pan",
            precio_unitario=Decimal("35"),
            cantidad=2, subtotal=Decimal("70"),
        )
        assert item.titulo == "Pan"
        assert item.imagen == ""


class TestPedido:
    def test_create_minimal(self):
        p = Pedido(
            id_pedido="p1", id_sesion="s1",
            total=Decimal("100"),
        )
        assert p.estado == "pendiente"
        assert p.items == []

    def test_fecha_property(self):
        p = Pedido(
            id_pedido="p1", id_sesion="s1",
            total=Decimal("100"),
            created_at=datetime(2024, 3, 15, 10, 30, tzinfo=timezone.utc),
        )
        assert p.fecha == "15/03/2024 10:30"

    def test_fecha_none(self):
        p = Pedido(
            id_pedido="p1", id_sesion="s1",
            total=Decimal("100"),
        )
        assert p.fecha is None

    def test_estado_label(self):
        p = Pedido(id_pedido="p1", id_sesion="s1", total=Decimal("100"), estado="entregado")
        assert p.estado_label == "Entregado"

    def test_estado_label_unknown(self):
        p = Pedido(id_pedido="p1", id_sesion="s1", total=Decimal("100"), estado="unknown")
        assert p.estado_label == "unknown"

    def test_estado_labels_all(self):
        estados = {
            "pendiente": "Pendiente",
            "confirmado": "Confirmado",
            "entregado": "Entregado",
            "cancelado": "Cancelado",
        }
        for estado, label in estados.items():
            p = Pedido(id_pedido="p1", id_sesion="s1", total=Decimal("100"), estado=estado)
            assert p.estado_label == label
