"""Benchmarks: response latency for key routes."""

import pytest
from unittest.mock import AsyncMock
from conftest import fake_record
from decimal import Decimal


class TestLatency:
    def test_home_page(self, benchmark, client):
        response = benchmark(client.get, "/")
        assert response.status_code == 200

    def test_login_form(self, benchmark, client):
        response = benchmark(client.get, "/auth/login")
        assert response.status_code == 200

    def test_register_form(self, benchmark, client):
        response = benchmark(client.get, "/auth/register")
        assert response.status_code == 200

    def test_inicio_section(self, benchmark, client):
        response = benchmark(client.get, "/section/inicio")
        assert response.status_code == 200

    def test_servicios_section(self, benchmark, client):
        response = benchmark(client.get, "/section/servicios")
        assert response.status_code == 200

    def test_contacto_section(self, benchmark, client):
        response = benchmark(client.get, "/section/contacto")
        assert response.status_code == 200

    def test_cart_page(self, benchmark, client):
        response = benchmark(client.get, "/carrito")
        assert response.status_code == 200

    def test_product_api(self, benchmark, client):
        response = benchmark(client.get, "/api/productos/pan-dulce")
        assert response.status_code == 200

    def test_perfil_guest(self, benchmark, client):
        response = benchmark(client.get, "/perfil")
        assert response.status_code == 200

    def test_perfil_logged_in(self, benchmark, client, app):
        application, mock_db = app
        mock_db.fetchrow.return_value = fake_record({
            "id_usuario": "u1", "id_sesion": "bench-session-uuid-00000000",
            "nombre": "Alice", "email": "alice@test.com",
            "avatar": "", "created_at": None,
        })
        response = benchmark(client.get, "/perfil")
        assert response.status_code == 200
        assert "Alice" in response.text

    def test_static_css(self, benchmark, client):
        response = benchmark(client.get, "/static/css/output.css?v=2")
        assert response.status_code in (200, 404)

    def test_htmx_js(self, benchmark, client):
        response = benchmark(client.get, "/static/js/htmx.min.js")
        assert response.status_code in (200, 404)
