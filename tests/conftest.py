import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any
from decimal import Decimal
from datetime import datetime, timezone
from dataclasses import dataclass, field

from database import Database
from models import User, UserWithPsw, Carrito, CarritoItem, Pedido, PedidoItem
from repos.user_repo import UserRepo
from repos.cart_repo import CartRepo
from repos.product_repo import ProductRepo
from config import SLUG_TO_CATEGORIA, CATEGORIA_TO_NOMBRE
from repos.order_repo import OrderRepo
from auth import hash_password, verify_password
from forms import RegisterForm, LoginForm


# ─── Factories ─────────────────────────────────────────────


def make_user(**kwargs) -> User:
    defaults = {
        "id_usuario": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "id_sesion": "11111111-2222-3333-4444-555555555555",
        "nombre": "Test User",
        "email": "test@example.com",
        "avatar": "",
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return User(**defaults)


def make_user_with_psw(**kwargs) -> UserWithPsw:
    psw_defaults = {"password_hash": hash_password("secret123")}
    psw_defaults.update(kwargs)
    base = make_user()
    return UserWithPsw(**base.model_dump(), **psw_defaults)


def make_carrito_item(**kwargs) -> CarritoItem:
    defaults = {
        "id_item": "item-0001-0000-0000-000000000001",
        "id_carrito": "cart-0001-0000-0000-000000000001",
        "id_producto": 1,
        "titulo": "Pan de Muerto",
        "descripcion": "",
        "imagen": "",
        "precio_unitario": Decimal("35.00"),
        "cantidad": 2,
        "subtotal": Decimal("70.00"),
    }
    defaults.update(kwargs)
    return CarritoItem(**defaults)


def make_carrito(**kwargs) -> Carrito:
    defaults = {
        "id_carrito": "cart-0001-0000-0000-000000000001",
        "id_sesion": "11111111-2222-3333-4444-555555555555",
        "estado": "activo",
        "items": [],
    }
    defaults.update(kwargs)
    return Carrito(**defaults)


def make_pedido(**kwargs) -> Pedido:
    defaults = {
        "id_pedido": "order-0001-0000-0000-000000000001",
        "id_sesion": "11111111-2222-3333-4444-555555555555",
        "id_usuario": None,
        "estado": "pendiente",
        "total": Decimal("70.00"),
        "cantidad_items": 1,
        "cantidad_productos": 2,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "items": [],
    }
    defaults.update(kwargs)
    return Pedido(**defaults)


# ─── Mock Database ─────────────────────────────────────────


class MockAsyncRow(dict):
    """Simula una fila asyncpg: accesible por índice y por clave."""
    def __getitem__(self, key):
        if isinstance(key, int):
            keys = list(self.keys())
            return self[keys[key]]
        return super().__getitem__(key)


@dataclass
class FakeRecord:
    """Simula un asyncpg Record (dict-like + index access)."""
    _data: dict = field(default_factory=dict)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __iter__(self):
        return iter(self.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            keys = list(self._data.keys())
            return self._data[keys[key]]
        return self._data[key]

    def __getattr__(self, key):
        if key in self._data:
            return self._data[key]
        raise AttributeError(key)

    def __len__(self):
        return len(self._data)


def fake_record(data: dict) -> FakeRecord:
    return FakeRecord(_data=data)


# ─── Fixtures compartidos ──────────────────────────────────


@pytest.fixture
def mock_fetchrow():
    return AsyncMock()


@pytest.fixture
def mock_fetch():
    return AsyncMock()


@pytest.fixture
def mock_execute():
    return AsyncMock()


@pytest.fixture
def mock_db(mock_fetchrow, mock_fetch, mock_execute):
    db = MagicMock(spec=Database)
    db.fetchrow = mock_fetchrow
    db.fetch = mock_fetch
    db.execute = mock_execute

    trans_conn = MagicMock()
    trans_conn.fetchrow = AsyncMock(return_value=fake_record({"id_pedido": "order-1", "created_at": None}))
    trans_conn.fetch = AsyncMock(return_value=[])
    trans_conn.execute = AsyncMock(return_value="OK")

    trans_cm = MagicMock()
    trans_cm.__aenter__ = AsyncMock(return_value=trans_conn)
    trans_cm.__aexit__ = AsyncMock(return_value=None)
    db.transaction = AsyncMock(return_value=trans_cm)

    return db


@pytest.fixture
def user_repo(mock_db):
    return UserRepo(mock_db)


@pytest.fixture
def cart_repo(mock_db):
    return CartRepo(mock_db)


@pytest.fixture
def product_repo(mock_db):
    return ProductRepo(mock_db)


@pytest.fixture
def order_repo(mock_db):
    return OrderRepo(mock_db)
