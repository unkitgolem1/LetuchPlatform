from repos.interfaces import DatabaseInterface
from config import SLUG_TO_CATEGORIA, CATEGORIA_TO_NOMBRE


class ProductRepo:
    def __init__(self, db: DatabaseInterface):
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
