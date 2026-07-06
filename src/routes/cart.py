"""Cart routes: profile, cart display, add/remove items."""

from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from models import User
from .deps import (
    templates,
    get_session,
    get_current_user,
    get_user_repo,
    get_cart_service,
    get_order_service,
    servir_perfil_response,
)
from utils import parse_request_body

router = APIRouter()


@router.get("/perfil", response_class=HTMLResponse)
async def servir_perfil(
    request: Request,
    session_id: str = Depends(get_session),
    repo = Depends(get_user_repo),
):
    return await servir_perfil_response(request, session_id, repo)


@router.get("/carrito", response_class=HTMLResponse)
async def servir_carrito(
    request: Request,
    session_id: str = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user),
    cart_service = Depends(get_cart_service),
):
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="sections/login.html",
            context={"errors": []},
        )
    cart = await cart_service.get_cart(session_id)
    return templates.TemplateResponse(
        request=request,
        name="sections/carrito.html",
        context={
            "items": cart.items if cart else [],
            "total": float(cart.total) if cart else 0,
        },
    )


@router.post("/carrito_db", response_class=HTMLResponse)
async def carrito_post(
    request: Request,
    session_id: str = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user),
    cart_service = Depends(get_cart_service),
    order_service = Depends(get_order_service),
):
    data = await parse_request_body(request)
    accion = data.get("accion", "")

    if accion == "checkout":
        if current_user is None:
            return templates.TemplateResponse(
                request=request,
                name="sections/login.html",
                context={"errors": [{"field": "", "msg": "Inicia sesión para pagar"}]},
            )
        pedido = await order_service.checkout(session_id)
        return templates.TemplateResponse(
            request=request,
            name="sections/checkout-confirmacion.html",
            context={"pedido": pedido},
        )
    elif accion == "sumar":
        await cart_service.adjust_qty(session_id, data["id_item"], 1)
    elif accion == "restar":
        await cart_service.adjust_qty(session_id, data["id_item"], -1)
    elif "id" in data:
        await cart_service.add_item(
            session_id, int(data["id"]), int(data.get("cantidad", 1))
        )

    cart = await cart_service.get_cart(session_id)
    return templates.TemplateResponse(
        request=request,
        name="sections/carrito.html",
        context={
            "items": cart.items if cart else [],
            "total": float(cart.total) if cart else 0,
        },
    )
