"""Integration tests for OrderRepo — uses mocked Database."""

import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
from repos.order_repo import OrderRepo
from models import Pedido
from conftest import fake_record


SESSION_ID = "11111111-2222-3333-4444-555555555555"


class TestCreateFromCart:
    async def test_raises_when_no_active_cart(self, order_repo, mock_fetchrow):
        mock_fetchrow.return_value = None
        with pytest.raises(ValueError, match="No hay carrito activo"):
            await order_repo.create_from_cart(SESSION_ID)

    async def test_raises_when_cart_empty(self, order_repo, mock_fetchrow, mock_fetch):
        mock_fetchrow.return_value = fake_record({"id_carrito": "c1"})
        mock_fetch.return_value = []
        with pytest.raises(ValueError, match="Carrito vacío"):
            await order_repo.create_from_cart(SESSION_ID)

    async def test_creates_order_with_items(self, order_repo, mock_fetchrow, mock_fetch):
        # Cart items fetch, then get_detail's item fetch
        mock_fetch.side_effect = [
            # First fetch: cart items (used in transaction)
            [
                fake_record({
                    "id_producto": 1, "cantidad": 2, "precio_unitario": Decimal("35.00"),
                    "nombre": "Pan de Muerto", "imagen": "",
                }),
            ],
            # Second fetch: get_detail's pedido_items
            [
                fake_record({
                    "id_pedido_item": "pi1", "id_pedido": "order-1",
                    "id_producto": 1, "titulo": "Pan de Muerto",
                    "precio_unitario": Decimal("35.00"), "cantidad": 2,
                    "subtotal": Decimal("70.00"), "imagen": "",
                    "created_at": None,
                }),
            ],
        ]
        mock_fetchrow.side_effect = [
            fake_record({"id_carrito": "c1"}),                          # fetchrow: carrito activo
            fake_record({"id_usuario": "u1"}),                          # fetchrow: usuario vinculado
            fake_record({                                               # get_detail: pedido
                "id_pedido": "order-1", "id_sesion": SESSION_ID, "id_usuario": "u1",
                "estado": "pendiente", "total": Decimal("70.00"),
                "cantidad_items": 1, "cantidad_productos": 2,
                "created_at": None, "updated_at": None,
            }),
        ]

        pedido = await order_repo.create_from_cart(SESSION_ID)
        assert isinstance(pedido, Pedido)
        assert pedido.total == Decimal("70.00")
        assert len(pedido.items) == 1
        assert pedido.items[0].titulo == "Pan de Muerto"

    async def test_order_links_user_if_logged_in(self, order_repo, mock_fetchrow, mock_fetch):
        mock_fetch.side_effect = [
            [
                fake_record({
                    "id_producto": 1, "cantidad": 1, "precio_unitario": Decimal("10.00"),
                    "nombre": "Item", "imagen": "",
                }),
            ],
            [
                fake_record({
                    "id_pedido_item": "pi1", "id_pedido": "order-1",
                    "id_producto": 1, "titulo": "Item",
                    "precio_unitario": Decimal("10.00"), "cantidad": 1,
                    "subtotal": Decimal("10.00"), "imagen": "",
                    "created_at": None,
                }),
            ],
        ]
        mock_fetchrow.side_effect = [
            fake_record({"id_carrito": "c1"}),
            fake_record({"id_usuario": "user-123"}),
            fake_record({
                "id_pedido": "order-1", "id_sesion": SESSION_ID, "id_usuario": "user-123",
                "estado": "pendiente", "total": Decimal("10.00"),
                "cantidad_items": 1, "cantidad_productos": 1,
                "created_at": None, "updated_at": None,
            }),
        ]

        pedido = await order_repo.create_from_cart(SESSION_ID)
        assert pedido.id_usuario == "user-123"


class TestGetBySession:
    async def test_returns_orders(self, order_repo, mock_fetch):
        mock_fetch.return_value = [
            fake_record({
                "id_pedido": "p1", "id_sesion": SESSION_ID, "id_usuario": None,
                "estado": "pendiente", "total": Decimal("50.00"),
                "cantidad_items": 2, "cantidad_productos": 3,
                "created_at": None,
            }),
        ]
        pedidos = await order_repo.get_by_session(SESSION_ID)
        assert len(pedidos) == 1
        assert pedidos[0].total == Decimal("50.00")

    async def test_returns_empty_list(self, order_repo, mock_fetch):
        mock_fetch.return_value = []
        pedidos = await order_repo.get_by_session("no-orders")
        assert pedidos == []


class TestGetDetail:
    async def test_returns_pedido_with_items(self, order_repo, mock_fetchrow, mock_fetch):
        mock_fetchrow.return_value = fake_record({
            "id_pedido": "p1", "id_sesion": SESSION_ID, "id_usuario": None,
            "estado": "pendiente", "total": Decimal("70.00"),
            "cantidad_items": 1, "cantidad_productos": 2,
            "created_at": None, "updated_at": None,
        })
        mock_fetch.return_value = [
            fake_record({
                "id_pedido_item": "pi1", "id_pedido": "p1",
                "id_producto": 1, "titulo": "Pan",
                "precio_unitario": Decimal("35.00"), "cantidad": 2,
                "subtotal": Decimal("70.00"), "imagen": "",
                "created_at": None,
            }),
        ]
        pedido = await order_repo.get_detail("p1", SESSION_ID)
        assert pedido is not None
        assert len(pedido.items) == 1
        assert pedido.items[0].titulo == "Pan"

    async def test_returns_none_for_other_session(self, order_repo, mock_fetchrow):
        mock_fetchrow.return_value = None
        pedido = await order_repo.get_detail("p1", "other-session")
        assert pedido is None
