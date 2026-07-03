from database import Database
from models import Pedido, PedidoItem
from decimal import Decimal
from typing import Optional


class OrderRepo:
    def __init__(self, db: Database):
        self.db = db

    async def create_from_cart(self, session_id: str) -> Pedido:
        """Crea un pedido desde el carrito activo. Transaccional."""
        cart = await self.db.fetchrow(
            """
            SELECT id_carrito FROM carritos
            WHERE id_sesion = $1::uuid AND estado = 'activo'
            """,
            session_id,
        )
        if not cart:
            raise ValueError("No hay carrito activo")

        items = await self.db.fetch(
            """
            SELECT ic.id_producto, ic.cantidad, ic.precio_unitario,
                   p.nombre, COALESCE(p.imagen, '') AS imagen
            FROM items_carrito ic
            JOIN productos p ON p.id = ic.id_producto
            WHERE ic.id_carrito = $1::uuid
            """,
            cart["id_carrito"],
        )
        if not items:
            raise ValueError("Carrito vacío")

        user_row = await self.db.fetchrow(
            "SELECT id_usuario FROM usuarios WHERE id_sesion = $1::uuid",
            session_id,
        )
        user_id = str(user_row["id_usuario"]) if user_row else None

        total = sum(
            Decimal(str(r["precio_unitario"])) * r["cantidad"]
            for r in items
        )

        async with await self.db.transaction() as conn:
            order_row = await conn.fetchrow(
                """
                INSERT INTO pedidos (id_sesion, id_usuario, total)
                VALUES ($1::uuid, $2::uuid, $3)
                RETURNING id_pedido, created_at
                """,
                session_id, user_id, total,
            )
            order_id = str(order_row["id_pedido"])

            for item in items:
                subtotal = Decimal(str(item["precio_unitario"])) * item["cantidad"]
                await conn.execute(
                    """
                    INSERT INTO pedido_items
                        (id_pedido, id_producto, titulo, imagen, precio_unitario, cantidad, subtotal)
                    VALUES ($1::uuid, $2, $3, $4, $5, $6, $7)
                    """,
                    order_id, item["id_producto"], item["nombre"],
                    item["imagen"], item["precio_unitario"], item["cantidad"], subtotal,
                )
                await conn.execute(
                    """
                    UPDATE productos
                    SET cantidad_stock = GREATEST(cantidad_stock - $1, 0)
                    WHERE id = $2
                    """,
                    item["cantidad"], item["id_producto"],
                )

            await conn.execute(
                """
                UPDATE carritos
                SET estado = 'convertido', updated_at = NOW()
                WHERE id_carrito = $1::uuid
                """,
                cart["id_carrito"],
            )

        return await self.get_detail(order_id, session_id)

    async def mark_as_paid(self, order_id: str, session_id: str) -> Optional[Pedido]:
        """Mock pago: cambia estado a 'confirmado'."""
        row = await self.db.fetchrow(
            """
            UPDATE pedidos
            SET estado = 'confirmado', updated_at = NOW()
            WHERE id_pedido = $1::uuid AND id_sesion = $2::uuid AND estado = 'pendiente'
            RETURNING id_pedido
            """,
            order_id, session_id,
        )
        if not row:
            return None
        return await self.get_detail(order_id, session_id)

    async def get_by_session(self, session_id: str) -> list[Pedido]:
        rows = await self.db.fetch(
            "SELECT * FROM vista_pedidos WHERE id_sesion = $1::uuid",
            session_id,
        )
        return [Pedido(**dict(r)) for r in rows]

    async def get_detail(self, order_id: str, session_id: str) -> Optional[Pedido]:
        row = await self.db.fetchrow(
            "SELECT * FROM pedidos WHERE id_pedido = $1::uuid AND id_sesion = $2::uuid",
            order_id, session_id,
        )
        if not row:
            return None
        item_rows = await self.db.fetch(
            """
            SELECT * FROM pedido_items
            WHERE id_pedido = $1::uuid
            ORDER BY created_at
            """,
            order_id,
        )
        return Pedido(
            **dict(row),
            items=[PedidoItem(**dict(r)) for r in item_rows],
        )
