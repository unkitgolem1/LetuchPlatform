"""Order routes: payment, order listing, order detail."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from .deps import templates, get_session, get_order_service
from utils import parse_request_body

router = APIRouter()


@router.post("/pagar", response_class=HTMLResponse)
async def pagar(
    request: Request,
    session_id: str = Depends(get_session),
    order_service = Depends(get_order_service),
):
    data = await parse_request_body(request)
    order_id = data.get("order_id", "")
    pedido = await order_service.pay(order_id, session_id)
    if not pedido:
        return templates.TemplateResponse(
            request=request,
            name="sections/pago-fallido.html",
            context={"error": "Pedido no encontrado o ya procesado"},
        )
    return templates.TemplateResponse(
        request=request,
        name="sections/pago-exitoso.html",
        context={"pedido": pedido},
    )


@router.get("/mis-pedidos", response_class=HTMLResponse)
async def servir_mis_pedidos(
    request: Request,
    session_id: str = Depends(get_session),
    order_service = Depends(get_order_service),
):
    pedidos = await order_service.get_orders(session_id)
    return templates.TemplateResponse(
        request=request,
        name="sections/mis_pedidos.html",
        context={"pedidos": pedidos},
    )


@router.get("/section/pedido/{id}", response_class=HTMLResponse)
async def servir_pedido(
    request: Request,
    id: str,
    session_id: str = Depends(get_session),
    order_service = Depends(get_order_service),
):
    pedido = await order_service.get_order_detail(id, session_id)
    if not pedido:
        return templates.TemplateResponse(
            request=request,
            name="sections/mis_pedidos.html",
            context={"pedidos": []},
        )
    return templates.TemplateResponse(
        request=request,
        name="sections/pedido_detalle.html",
        context={"pedido": pedido},
    )
