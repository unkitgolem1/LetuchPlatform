"""Integration tests for ProductRepo — uses mocked Database."""

import pytest
from unittest.mock import AsyncMock
from repos.product_repo import ProductRepo, SLUG_TO_CATEGORIA, CATEGORIA_TO_NOMBRE
from tests.conftest import fake_record


class TestGetBySlug:
    async def test_returns_products_and_name(self, product_repo, mock_fetch):
        mock_fetch.return_value = [
            fake_record({
                "id": 1, "titulo": "Concha", "descripcion": "Dulce",
                "imagen": "", "precio": 15.0, "cantidad": 10,
            }),
            fake_record({
                "id": 2, "titulo": "Oreja", "descripcion": "Hojaldrada",
                "imagen": "", "precio": 12.0, "cantidad": 5,
            }),
        ]
        productos, nombre = await product_repo.get_by_slug("pan-dulce")
        assert nombre == "Pan Dulce"
        assert len(productos) == 2
        assert productos[0]["titulo"] == "Concha"
        assert productos[1]["precio"] == 12.0

    async def test_returns_empty_for_unknown_slug(self, product_repo, mock_fetch):
        productos, nombre = await product_repo.get_by_slug("unknown-slug")
        assert productos == []
        assert nombre == "unknown-slug"
        mock_fetch.assert_not_awaited()

    async def test_returns_empty_when_no_products(self, product_repo, mock_fetch):
        mock_fetch.return_value = []
        productos, nombre = await product_repo.get_by_slug("bebidas")
        assert productos == []
        assert nombre == "Bebidas"

    async def test_product_fields_structure(self, product_repo, mock_fetch):
        mock_fetch.return_value = [
            fake_record({
                "id": 1, "titulo": "Café", "descripcion": "Caliente",
                "imagen": "img.jpg", "precio": 25.0, "cantidad": 20,
            }),
        ]
        productos, _ = await product_repo.get_by_slug("bebidas")
        p = productos[0]
        assert "id" in p
        assert "titulo" in p
        assert "precio" in p
        assert isinstance(p["precio"], float)

    async def test_all_slugs_have_categoria(self):
        for slug in SLUG_TO_CATEGORIA:
            assert slug in SLUG_TO_CATEGORIA

    async def test_all_categorias_have_nombre(self):
        for cat in CATEGORIA_TO_NOMBRE:
            assert cat in CATEGORIA_TO_NOMBRE

    async def test_slug_to_categoria_mapping_consistent(self):
        """Cada slug debe mapear a una categoría que tenga nombre display."""
        for categoria in SLUG_TO_CATEGORIA.values():
            assert categoria in CATEGORIA_TO_NOMBRE, (
                f"La categoría '{categoria}' no tiene nombre display"
            )


class TestGetById:
    async def test_returns_product(self, product_repo, mock_fetchrow):
        mock_fetchrow.return_value = fake_record({
            "id": 1, "titulo": "Concha", "descripcion": "Rica",
            "imagen": "", "precio": 15.0, "cantidad": 10,
        })
        prod = await product_repo.get_by_id("1")
        assert prod is not None
        assert prod["titulo"] == "Concha"
        assert prod["precio"] == 15.0

    async def test_returns_none(self, product_repo, mock_fetchrow):
        mock_fetchrow.return_value = None
        prod = await product_repo.get_by_id("999")
        assert prod is None
