"""Order use cases: checkout, payment, order history."""

from typing import Optional
from repos.order_repo import OrderRepo
from models import Pedido


class OrderService:
    def __init__(self, order_repo: OrderRepo):
        self.order_repo = order_repo

    async def checkout(self, session_id: str) -> Pedido:
        """Create order from active cart. Raises ValueError if cart is empty."""
        return await self.order_repo.create_from_cart(session_id)

    async def pay(self, order_id: str, session_id: str) -> Optional[Pedido]:
        """Mark pending order as paid (confirmed)."""
        return await self.order_repo.mark_as_paid(order_id, session_id)

    async def get_orders(self, session_id: str) -> list[Pedido]:
        """Return all orders for the current session."""
        return await self.order_repo.get_by_session(session_id)

    async def get_order_detail(
        self, order_id: str, session_id: str
    ) -> Optional[Pedido]:
        """Return order details including items."""
        return await self.order_repo.get_detail(order_id, session_id)
