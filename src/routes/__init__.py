"""Routes package — assembles all sub-routers into a single router.

Usage:
    from routes import router
    app.include_router(router)
"""

from fastapi import APIRouter, Depends

from .deps import ensure_session
from . import static, products, cart, orders, auth

router = APIRouter(dependencies=[Depends(ensure_session)])

router.include_router(static.router)
router.include_router(products.router)
router.include_router(cart.router)
router.include_router(orders.router)
router.include_router(auth.router)
