from database import Database

SLUG_TO_CATEGORIA = {
    "pan-dulce": "PANADERIA DULCE",
    "pan-salado": "PANADERIA SALADA",
    "platillos": "DESAYUNO-CENA",
    "bebidas": "BEBIDAS CALIENTES",
    "bebidas-frias": "BEBIDAS FRIAS",
    "productos-locales": "PRODUCTOS LOCALES",
    "postres": "POSTRES",
    "temporada": "PAN DE TEMPORADA",
}

CATEGORIA_TO_NOMBRE = {
    "PANADERIA DULCE": "Pan Dulce",
    "PANADERIA SALADA": "Pan Salado",
    "DESAYUNO-CENA": "Platillos",
    "BEBIDAS CALIENTES": "Bebidas",
    "BEBIDAS FRIAS": "Bebidas Frías",
    "PRODUCTOS LOCALES": "Productos Locales",
    "POSTRES": "Postres",
    "PAN DE TEMPORADA": "Pan de Temporada",
}


class ProductRepo:
    def __init__(self, db: Database):
        self.db = db

    async def get_by_slug(self, slug: str) -> tuple[list[dict], str]:
        categoria_db = SLUG_TO_CATEGORIA.get(slug)
        if not categoria_db:
            return [], slug

        rows = await self.db.fetch(
            """
            SELECT id, nombre AS titulo, descripcion,
                   COALESCE(imagen, '') AS imagen,
                   precio, cantidad_stock AS cantidad
            FROM productos
            WHERE categoria = $1 AND activo = TRUE
            ORDER BY nombre
            """,
            categoria_db,
        )
        productos = [
            {
                "id": str(r["id"]),
                "titulo": r["titulo"],
                "descripcion": r["descripcion"] or "",
                "imagen": r["imagen"],
                "precio": float(r["precio"]),
                "cantidad": r["cantidad"] or 0,
            }
            for r in rows
        ]
        nombre = CATEGORIA_TO_NOMBRE.get(categoria_db, categoria_db)
        return productos, nombre

    async def get_by_id(self, producto_id: str) -> dict | None:
        row = await self.db.fetchrow(
            """
            SELECT id, nombre AS titulo, descripcion,
                   COALESCE(imagen, '') AS imagen,
                   precio, cantidad_stock AS cantidad
            FROM productos
            WHERE id = $1::bigint AND activo = TRUE
            """,
            producto_id,
        )
        if not row:
            return None
        return {
            "id": str(row["id"]),
            "titulo": row["titulo"],
            "descripcion": row["descripcion"] or "",
            "imagen": row["imagen"],
            "precio": float(row["precio"]),
            "cantidad": row["cantidad"] or 0,
        }
