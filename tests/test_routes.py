"""Integration tests for routes (session, auth, cart) — uses mocked DB & TestClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from pathlib import Path
from routes import router
from routes.deps import get_db, ensure_session, get_current_user
from database import Database
from fastapi.templating import Jinja2Templates
from conftest import fake_record
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = str(BASE_DIR / "static" / "templates")


@pytest.fixture
def app():
    application = FastAPI()

    mock_db = MagicMock(spec=Database)
    mock_db.fetchrow = AsyncMock(return_value=None)
    mock_db.fetch = AsyncMock(return_value=[])
    mock_db.execute = AsyncMock(return_value="OK")
    mock_db.transaction = AsyncMock()

    async def mock_ensure_session(
        request: Request,
    ):
        request.state.session_id = "test-session-uuid-000000000000"

    application.dependency_overrides[ensure_session] = mock_ensure_session

    async def mock_get_db():
        return mock_db

    application.dependency_overrides[get_db] = mock_get_db

    application.include_router(router)

    static_dir = BASE_DIR / "static"
    if static_dir.exists():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return application, mock_db


@pytest.fixture
def client(app):
    application, _ = app
    with TestClient(application) as c:
        yield c


class TestRoot:
    def test_get_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_sections_return_200(self, client):
        for section in ("/section/inicio", "/section/servicios", "/section/contacto"):
            response = client.get(section)
            assert response.status_code == 200


class TestSession:
    def test_session_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200


class TestAuthRoutes:
    def test_login_form_returns_200(self, client):
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_register_form_returns_200(self, client):
        response = client.get("/auth/register")
        assert response.status_code == 200


class TestProfile:
    def test_perfil_logged_out(self, client):
        """Sin sesión activa, se ve la vista de invitado."""
        response = client.get("/perfil")
        assert response.status_code == 200

    def test_perfil_logged_in(self, client, app):
        application, mock_db = app
        mock_db.fetchrow.return_value = fake_record({
            "id_usuario": "u1", "id_sesion": "s1",
            "nombre": "Alice", "email": "alice@test.com",
            "avatar": "", "created_at": None,
        })
        response = client.get("/perfil")
        assert response.status_code == 200
        assert "Alice" in response.text


class TestCart:
    def test_cart_without_login_shows_login(self, client):
        response = client.get("/carrito")
        assert response.status_code == 200
        assert "Iniciar" in response.text or "login" in response.text.lower()


class TestProductAPI:
    def test_productos_returns_200(self, client):
        response = client.get("/api/productos/pan-dulce")
        assert response.status_code == 200

    def test_productos_unknown_slug(self, client):
        response = client.get("/api/productos/unknown")
        assert response.status_code == 200


class TestCartPost:
    def test_cart_add_item_as_guest(self, client, app):
        """Invitados pueden agregar items al carrito."""
        application, mock_db = app
        mock_db.fetchrow.side_effect = [
            None,                                               # get_current_user → guest
            fake_record({"id": "cart-uuid"}),                   # get_or_create_cart_id
            fake_record({"precio": Decimal("25.00")}),          # SELECT precio
            fake_record({"id_carrito": "c1", "id_sesion": "s",  # get_detail: carrito
                         "estado": "activo"}),
        ]
        mock_db.fetch.return_value = []
        response = client.post("/carrito_db", json={"id": 1, "cantidad": 2})
        assert response.status_code == 200

    def test_checkout_without_login_shows_login(self, client):
        response = client.post("/carrito_db", json={"accion": "checkout"})
        assert response.status_code == 200
        assert "Inicia sesión" in response.text

    def test_checkout_logged_in(self, client, app):
        application, mock_db = app

        mock_db.fetchrow.side_effect = [
            fake_record({"id_usuario": "u1", "id_sesion": "s1",       # get_current_user
                         "nombre": "Alice", "email": "a@b.com",
                         "avatar": "", "created_at": None}),
            fake_record({"id_carrito": "c1"}),                          # create_from_cart: carrito
            fake_record({"id_usuario": "u1"}),                          # create_from_cart: usuario
            fake_record({                                               # get_detail: pedido
                "id_pedido": "order-1", "id_sesion": "s1", "id_usuario": "u1",
                "estado": "pendiente", "total": Decimal("70.00"),
                "cantidad_items": 1, "cantidad_productos": 2,
                "created_at": None, "updated_at": None,
            }),
        ]
        mock_db.fetch.side_effect = [
            [
                fake_record({
                    "id_producto": 1, "cantidad": 2, "precio_unitario": Decimal("35.00"),
                    "nombre": "Pan", "imagen": "",
                }),
            ],
            [
                fake_record({
                    "id_pedido_item": "pi1", "id_pedido": "order-1",
                    "id_producto": 1, "titulo": "Pan",
                    "precio_unitario": Decimal("35.00"), "cantidad": 2,
                    "subtotal": Decimal("70.00"), "imagen": "",
                    "created_at": None,
                }),
            ],
        ]

        class FakeConn:
            async def fetchrow(self, *a, **kw):
                return fake_record({"id_pedido": "order-1", "created_at": None})
            async def execute(self, *a, **kw):
                return "OK"

        mock_db.transaction.return_value.__aenter__ = AsyncMock(return_value=FakeConn())
        mock_db.transaction.return_value.__aexit__ = AsyncMock(return_value=None)

        response = client.post("/carrito_db", json={"accion": "checkout"})
        assert response.status_code == 200


class TestStatic:
    def test_static_css(self, client):
        response = client.get("/static/css/styles.css")
        assert response.status_code in (200, 404)
