"""Benchmarks: response payload size for key routes."""

import pytest


class TestResponseSize:
    def test_home_page_size(self, client):
        response = client.get("/")
        size_kb = len(response.content) / 1024
        print(f"\n  GET / → {size_kb:.2f} KB")
        assert response.status_code == 200

    def test_login_form_size(self, client):
        response = client.get("/auth/login")
        size_kb = len(response.content) / 1024
        print(f"\n  GET /auth/login → {size_kb:.2f} KB")
        assert response.status_code == 200

    def test_inicio_section_size(self, client):
        response = client.get("/section/inicio")
        size_kb = len(response.content) / 1024
        print(f"\n  GET /section/inicio → {size_kb:.2f} KB")
        assert response.status_code == 200

    def test_servicios_section_size(self, client):
        response = client.get("/section/servicios")
        size_kb = len(response.content) / 1024
        print(f"\n  GET /section/servicios → {size_kb:.2f} KB")
        assert response.status_code == 200

    def test_contacto_section_size(self, client):
        response = client.get("/section/contacto")
        size_kb = len(response.content) / 1024
        print(f"\n  GET /section/contacto → {size_kb:.2f} KB")
        assert response.status_code == 200

    def test_csp_headers_size(self, client):
        """Mide el tamaño extra que añaden los headers de seguridad."""
        response = client.get("/")
        csp = len(response.headers.get("Content-Security-Policy", ""))
        xcto = len(response.headers.get("X-Content-Type-Options", ""))
        xfo = len(response.headers.get("X-Frame-Options", ""))
        rp = len(response.headers.get("Referrer-Policy", ""))
        total = csp + xcto + xfo + rp
        print(f"\n  Security headers overhead: {total} bytes")
        assert response.status_code == 200

    def test_static_css_size(self, client):
        response = client.get("/static/css/output.css?v=2")
        size_kb = len(response.content) / 1024
        print(f"\n  GET /static/css/output.css → {size_kb:.2f} KB")
        assert response.status_code in (200, 404)

    def test_static_js_size(self, client):
        response = client.get("/static/js/htmx.min.js")
        size_kb = len(response.content) / 1024
        print(f"\n  GET /static/js/htmx.min.js → {size_kb:.2f} KB")
        assert response.status_code in (200, 404)
