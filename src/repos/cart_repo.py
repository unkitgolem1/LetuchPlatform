from database import Database
from models import Carrito, CarritoItem
from decimal import Decimal
from typing import Optional


class CartRepo:
    def __init__(self, db: Database):
        self.db = db

    async def get_or_create_cart_id(self, session_id: str) -> str:
        row = await self.db.fetchrow(
            "SELECT fn_obtener_o_crear_carrito($1::uuid) AS id",
            session_id,
        )
        return str(row["id"])

    async def get_detail(self, session_id: str) -> Optional[Carrito]:
        """Regresa el carrito activo con items, o None si no existe."""
        cart_row = await self.db.fetchrow(
            """
            SELECT id_carrito, id_sesion, estado
            FROM carritos
            WHERE id_sesion = $1::uuid AND estado = 'activo'
            """,
            session_id,
        )
        if not cart_row:
            return None

        item_rows = await self.db.fetch(
            """
            SELECT
                ic.id_item, ic.id_carrito, ic.id_producto,
                p.nombre AS titulo, COALESCE(p.descripcion, '') AS descripcion,
                COALESCE(p.imagen, '') AS imagen,
                ic.precio_unitario, ic.cantidad,
                (ic.precio_unitario * ic.cantidad)::numeric(12,2) AS subtotal
            FROM items_carrito ic
            JOIN productos p ON p.id = ic.id_producto
            WHERE ic.id_carrito = $1::uuid
            ORDER BY ic.created_at
            """,
            cart_row["id_carrito"],
        )

        items = [CarritoItem(**dict(r)) for r in item_rows]
        return Carrito(
            id_carrito=cart_row["id_carrito"],
            id_sesion=cart_row["id_sesion"],
            estado=cart_row["estado"],
            items=items,
        )

    async def add_item(
        self, session_id: str, producto_id: int, cantidad: int = 1
    ) -> None:
        """Agrega un producto al carrito activo. Si ya existe, suma cantidad."""
        cart_id = await self.get_or_create_cart_id(session_id)

        # Trae precio actual del producto
        prod = await self.db.fetchrow(
            "SELECT precio FROM productos WHERE id = $1", producto_id,
        )
        if not prod:
            return

        # Upsert: si el producto ya está en el carrito, suma cantidad
        await self.db.execute(
            """
            INSERT INTO items_carrito (id_carrito, id_producto, cantidad, precio_unitario)
            VALUES ($1::uuid, $2, $3, $4)
            ON CONFLICT (id_carrito, id_producto) DO UPDATE
                SET cantidad = items_carrito.cantidad + $3
            """,
            cart_id, producto_id, cantidad, prod["precio"],
        )

    async def update_qty(self, session_id: str, item_id: str, cantidad: int) -> None:
        """Actualiza cantidad de un item (0 = elimina)."""
        if cantidad <= 0:
            await self.db.execute(
                """
                DELETE FROM items_carrito
                WHERE id_item = $1::uuid
                  AND id_carrito IN (
                      SELECT id_carrito FROM carritos
                      WHERE id_sesion = $2::uuid AND estado = 'activo'
                  )
                """,
                item_id, session_id,
            )
        else:
            await self.db.execute(
                """
                UPDATE items_carrito
                SET cantidad = $1
                WHERE id_item = $2::uuid
                  AND id_carrito IN (
                      SELECT id_carrito FROM carritos
                      WHERE id_sesion = $3::uuid AND estado = 'activo'
                  )
                """,
                cantidad, item_id, session_id,
            )

    async def adjust_qty(self, session_id: str, item_id: str, delta: int) -> None:
        """Suma o resta delta a la cantidad actual. Si llega a 0, elimina."""
        if delta < 0:
            await self.db.execute(
                """
                UPDATE items_carrito
                SET cantidad = GREATEST(cantidad + $1, 0)
                WHERE id_item = $2::uuid
                  AND id_carrito IN (
                      SELECT id_carrito FROM carritos
                      WHERE id_sesion = $3::uuid AND estado = 'activo'
                  )
                """,
                delta, item_id, session_id,
            )
            # Limpia items con cantidad 0
            await self.db.execute(
                """
                DELETE FROM items_carrito
                WHERE cantidad <= 0
                  AND id_carrito IN (
                      SELECT id_carrito FROM carritos
                      WHERE id_sesion = $1::uuid AND estado = 'activo'
                  )
                """,
                session_id,
            )
        else:
            await self.db.execute(
                """
                UPDATE items_carrito
                SET cantidad = cantidad + $1
                WHERE id_item = $2::uuid
                  AND id_carrito IN (
                      SELECT id_carrito FROM carritos
                      WHERE id_sesion = $3::uuid AND estado = 'activo'
                  )
                """,
                delta, item_id, session_id,
            )

    async def remove_item(self, session_id: str, item_id: str) -> None:
        await self.db.execute(
            """
            DELETE FROM items_carrito
            WHERE id_item = $1::uuid
              AND id_carrito IN (
                  SELECT id_carrito FROM carritos
                  WHERE id_sesion = $2::uuid AND estado = 'activo'
              )
            """,
            item_id, session_id,
        )

    async def clear(self, session_id: str) -> None:
        await self.db.execute(
            """
            DELETE FROM items_carrito
            WHERE id_carrito IN (
                SELECT id_carrito FROM carritos
                WHERE id_sesion = $1::uuid AND estado = 'activo'
            )
            """,
            session_id,
        )

    async def checkout(self, session_id: str) -> None:
        """Marca el carrito como 'convertido' (simula pedido)."""
        await self.db.execute(
            """
            UPDATE carritos
            SET estado = 'convertido', updated_at = NOW()
            WHERE id_sesion = $1::uuid AND estado = 'activo'
            """,
            session_id,
        )
