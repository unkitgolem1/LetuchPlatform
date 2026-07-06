"""Product catalog routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from .deps import templates, get_product_repo

router = APIRouter()


@router.get("/api/productos/{categoria}", response_class=HTMLResponse)
async def productos_por_categoria(
    request: Request,
    categoria: str,
    repo = Depends(get_product_repo),
):
    productos, nombre = await repo.get_by_slug(categoria)
    return templates.TemplateResponse(
        request=request,
        name="sections/fragmento_card.html",
        context={"productos": productos, "categoria": nombre},
    )
