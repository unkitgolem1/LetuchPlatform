"""Cart use cases: display, add items, adjust quantities."""

from typing import Optional
from repos.cart_repo import CartRepo
from repos.product_repo import ProductRepo
from models import Carrito


class CartService:
    def __init__(self, cart_repo: CartRepo, product_repo: ProductRepo):
        self.cart_repo = cart_repo
        self.product_repo = product_repo

    async def get_cart(self, session_id: str) -> Optional[Carrito]:
        """Return active cart with items, or None."""
        return await self.cart_repo.get_detail(session_id)

    async def add_item(
        self, session_id: str, product_id: int, cantidad: int = 1
    ) -> None:
        """Add product to cart or increment quantity."""
        await self.cart_repo.add_item(session_id, product_id, cantidad)

    async def adjust_qty(self, session_id: str, item_id: str, delta: int) -> None:
        """Increase or decrease item quantity."""
        await self.cart_repo.adjust_qty(session_id, item_id, delta)
