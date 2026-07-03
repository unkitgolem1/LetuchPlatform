"""Integration tests for CartRepo — uses mocked Database."""

import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
from repos.cart_repo import CartRepo
from models import Carrito, CarritoItem
from tests.conftest import fake_record


SESSION_ID = "11111111-2222-3333-4444-555555555555"


class TestGetOrCreateCartId:
    async def test_returns_cart_id(self, cart_repo, mock_fetchrow):
        mock_fetchrow.return_value = fake_record({"id": "cart-uuid"})
        cart_id = await cart_repo.get_or_create_cart_id(SESSION_ID)
        assert cart_id == "cart-uuid"
        mock_fetchrow.assert_awaited_once()

    async def test_calls_function(self, cart_repo, mock_fetchrow):
        mock_fetchrow.return_value = fake_record({"id": "cid"})
        await cart_repo.get_or_create_cart_id(SESSION_ID)
        call_query = mock_fetchrow.await_args[0][0]
        assert "fn_obtener_o_crear_carrito" in call_query.lower()


class TestGetDetail:
    async def test_returns_none_when_no_cart(self, cart_repo, mock_fetchrow, mock_fetch):
        mock_fetchrow.return_value = None
        cart = await cart_repo.get_detail(SESSION_ID)
        assert cart is None

    async def test_returns_empty_cart(self, cart_repo, mock_fetchrow, mock_fetch):
        mock_fetchrow.return_value = fake_record({
            "id_carrito": "c1", "id_sesion": SESSION_ID, "estado": "activo",
        })
        mock_fetch.return_value = []
        cart = await cart_repo.get_detail(SESSION_ID)
        assert isinstance(cart, Carrito)
        assert cart.items == []
        assert cart.total == Decimal("0")

    async def test_returns_cart_with_items(self, cart_repo, mock_fetchrow, mock_fetch):
        mock_fetchrow.return_value = fake_record({
            "id_carrito": "c1", "id_sesion": SESSION_ID, "estado": "activo",
        })
        mock_fetch.return_value = [
            fake_record({
                "id_item": "i1", "id_carrito": "c1", "id_producto": 1,
                "titulo": "Pan", "descripcion": "", "imagen": "",
                "precio_unitario": Decimal("35.00"),
                "cantidad": 2,
                "subtotal": Decimal("70.00"),
            }),
        ]
        cart = await cart_repo.get_detail(SESSION_ID)
        assert len(cart.items) == 1
        assert cart.items[0].titulo == "Pan"
        assert cart.total == Decimal("70.00")


class TestAddItem:
    async def test_add_item_calls_upsert(self, cart_repo, mock_fetchrow, mock_execute):
        mock_fetchrow.side_effect = [
            fake_record({"id": "cart-uuid"}),       # get_or_create_cart_id
            fake_record({"precio": Decimal("25.00")}),  # SELECT precio
        ]
        mock_execute.return_value = "OK"
        await cart_repo.add_item(SESSION_ID, 1, 3)
        assert mock_fetchrow.await_count == 2
        assert mock_execute.await_count == 1
        call_query = mock_execute.await_args[0][0]
        assert "INSERT" in call_query.upper()
        assert "ON CONFLICT" in call_query.upper()

    async def test_add_nonexistent_product_does_nothing(self, cart_repo, mock_fetchrow, mock_execute):
        mock_fetchrow.side_effect = [
            fake_record({"id": "cart-uuid"}),
            None,  # producto no existe
        ]
        await cart_repo.add_item(SESSION_ID, 999, 1)
        assert mock_execute.await_count == 0


class TestAdjustQty:
    async def test_adjust_up(self, cart_repo, mock_execute):
        mock_execute.return_value = "OK"
        await cart_repo.adjust_qty(SESSION_ID, "item-1", 2)
        assert mock_execute.await_count == 1

    async def test_adjust_down(self, cart_repo, mock_execute):
        mock_execute.return_value = "OK"
        await cart_repo.adjust_qty(SESSION_ID, "item-1", -1)
        assert mock_execute.await_count >= 1

    async def test_adjust_down_cleans_zero(self, cart_repo, mock_execute):
        mock_execute.return_value = "OK"
        await cart_repo.adjust_qty(SESSION_ID, "item-1", -5)
        calls = mock_execute.await_args_list
        assert len(calls) >= 2
        last_query = calls[-1].args[0]
        assert "DELETE" in last_query.upper()


class TestRemoveItem:
    async def test_remove_item(self, cart_repo, mock_execute):
        mock_execute.return_value = "OK"
        await cart_repo.remove_item(SESSION_ID, "item-1")
        mock_execute.assert_awaited_once()
        call_query = mock_execute.await_args[0][0]
        assert "DELETE" in call_query.upper()


class TestClear:
    async def test_clear_cart(self, cart_repo, mock_execute):
        mock_execute.return_value = "OK"
        await cart_repo.clear(SESSION_ID)
        mock_execute.assert_awaited_once()
        call_query = mock_execute.await_args[0][0]
        assert "DELETE" in call_query.upper()


class TestCheckout:
    async def test_checkout_marks_converted(self, cart_repo, mock_execute):
        mock_execute.return_value = "OK"
        await cart_repo.checkout(SESSION_ID)
        mock_execute.assert_awaited_once()
        call_query = mock_execute.await_args[0][0]
        assert "UPDATE" in call_query.upper()
        assert "convertido" in call_query.lower()
