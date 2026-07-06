from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pathlib import Path
from pydantic import ValidationError
from database import Database
from repos.product_repo import ProductRepo
from repos.cart_repo import CartRepo
from repos.user_repo import UserRepo
from repos.order_repo import OrderRepo
from forms import RegisterForm, LoginForm
from auth import hash_password, verify_password
from models import User
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent


# ─── Session middleware (router-level) ──────────────────────


def get_db(request: Request) -> Database:
    return request.app.state.db


async def ensure_session(
    request: Request,
    db: Database = Depends(get_db),
) -> None:
    """Router-level dependency: resuelve session_id en request.state."""
    if request.url.path.startswith("/static/"):
        return
    cookie = request.cookies.get("session_id")
    try:
        row = await db.fetchrow(
            "SELECT fn_obtener_o_crear_sesion($1::uuid) AS id",
            cookie,
        )
        session_id = str(row["id"])
    except Exception:
        session_id = cookie if cookie else None

    if session_id:
        request.state.session_id = session_id
    else:
        request.state.session_id = ""


def get_session(request: Request) -> str:
    return request.state.session_id


router = APIRouter(dependencies=[Depends(ensure_session)])

templates = Jinja2Templates(directory=str(BASE_DIR / "static" / "templates"))


# ─── Repo dependencies ─────────────────────────────────────


def get_product_repo(db: Database = Depends(get_db)) -> ProductRepo:
    return ProductRepo(db)


def get_user_repo(db: Database = Depends(get_db)) -> UserRepo:
    return UserRepo(db)


def get_cart_repo(db: Database = Depends(get_db)) -> CartRepo:
    return CartRepo(db)


def get_order_repo(db: Database = Depends(get_db)) -> OrderRepo:
    return OrderRepo(db)


# ─── Auth helpers ──────────────────────────────────────────


async def get_current_user(
    session_id: str = Depends(get_session),
    repo: UserRepo = Depends(get_user_repo),
) -> Optional[User]:
    """Retorna el usuario vinculado a la sesión actual, o None."""
    return await repo.get_by_session(session_id)


async def login_required(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
) -> Optional[User]:
    """Dependencia: si no hay usuario autenticado, muestra el login."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Se necesita iniciar sesión")
    return current_user


# ─── Rutas ─────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def servir_template(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@router.get("/section/inicio", response_class=HTMLResponse)
async def inicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/inicio.html",
    )


@router.get("/api/productos/{categoria}", response_class=HTMLResponse)
async def productos_por_categoria(
    request: Request,
    categoria: str,
    repo: ProductRepo = Depends(get_product_repo),
):
    productos, nombre = await repo.get_by_slug(categoria)
    return templates.TemplateResponse(
        request=request,
        name="sections/fragmento_card.html",
        context={"productos": productos, "categoria": nombre},
    )


@router.get("/section/servicios", response_class=HTMLResponse)
async def servicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/servicios.html",
    )


@router.get("/section/contacto", response_class=HTMLResponse)
async def contacto(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/contacto.html",
    )


@router.get("/perfil", response_class=HTMLResponse)
async def servir_perfil(
    request: Request,
    session_id: str = Depends(get_session),
    repo: UserRepo = Depends(get_user_repo),
):
    user = await repo.get_by_session(session_id)
    return templates.TemplateResponse(
        request=request,
        name="sections/perfil.html",
        context={"user": user},
    )


@router.get("/carrito", response_class=HTMLResponse)
async def servir_carrito(
    request: Request,
    session_id: str = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user),
    repo: CartRepo = Depends(get_cart_repo),
):
    if current_user is None:
        return templates.TemplateResponse(
            request=request,
            name="sections/login.html",
            context={"errors": []},
        )
    cart = await repo.get_detail(session_id)
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
    cart_repo: CartRepo = Depends(get_cart_repo),
    order_repo: OrderRepo = Depends(get_order_repo),
):
    data: dict = {}
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        try:
            data = await request.json()
        except Exception:
            data = {}
    else:
        form = await request.form()
        data = dict(form)

    accion = data.get("accion", "")

    if accion == "checkout":
        if current_user is None:
            return templates.TemplateResponse(
                request=request,
                name="sections/login.html",
                context={"errors": [{"field": "", "msg": "Inicia sesión para pagar"}]},
            )
        pedido = await order_repo.create_from_cart(session_id)
        return templates.TemplateResponse(
            request=request,
            name="sections/checkout-confirmacion.html",
            context={"pedido": pedido},
        )
    elif accion == "sumar":
        await cart_repo.adjust_qty(session_id, data["id_item"], 1)
    elif accion == "restar":
        await cart_repo.adjust_qty(session_id, data["id_item"], -1)
    elif "id" in data:
        await cart_repo.add_item(
            session_id, int(data["id"]), int(data.get("cantidad", 1))
        )

    cart = await cart_repo.get_detail(session_id)
    return templates.TemplateResponse(
        request=request,
        name="sections/carrito.html",
        context={
            "items": cart.items if cart else [],
            "total": float(cart.total) if cart else 0,
        },
    )


@router.post("/pagar", response_class=HTMLResponse)
async def pagar(
    request: Request,
    session_id: str = Depends(get_session),
    order_repo: OrderRepo = Depends(get_order_repo),
):
    data: dict = {}
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        try:
            data = await request.json()
        except Exception:
            data = {}
    else:
        form = await request.form()
        data = dict(form)

    order_id = data.get("order_id", "")
    pedido = await order_repo.mark_as_paid(order_id, session_id)
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
    repo: OrderRepo = Depends(get_order_repo),
):
    pedidos = await repo.get_by_session(session_id)
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
    repo: OrderRepo = Depends(get_order_repo),
):
    pedido = await repo.get_detail(id, session_id)
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


# ─── Auth routes ───────────────────────────────────────────


@router.get("/robots.txt", response_class=Response)
async def robots_txt():
    content = """User-agent: *
Allow: /
Sitemap: https://letuchbakery.com/sitemap.xml
"""
    return Response(content=content.strip(), media_type="text/plain")


@router.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://letuchbakery.com/</loc>
        <priority>1.0</priority>
        <changefreq>weekly</changefreq>
    </url>
    <url>
        <loc>https://letuchbakery.com/section/inicio</loc>
        <priority>0.9</priority>
        <changefreq>weekly</changefreq>
    </url>
    <url>
        <loc>https://letuchbakery.com/section/servicios</loc>
        <priority>0.8</priority>
        <changefreq>monthly</changefreq>
    </url>
    <url>
        <loc>https://letuchbakery.com/section/contacto</loc>
        <priority>0.7</priority>
        <changefreq>monthly</changefreq>
    </url>
</urlset>"""
    return Response(content=content.strip(), media_type="application/xml")


@router.get("/auth/login", response_class=HTMLResponse)
async def auth_login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/login.html",
        context={"errors": []},
    )


@router.get("/auth/register", response_class=HTMLResponse)
async def auth_register_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/register.html",
        context={"errors": []},
    )


@router.post("/auth/login", response_class=HTMLResponse)
async def auth_login(
    request: Request,
    session_id: str = Depends(get_session),
    db: Database = Depends(get_db),
    user_repo: UserRepo = Depends(get_user_repo),
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        form = LoginForm(email=email, password=password)
    except ValidationError as e:
        errors = [{"field": err["loc"][0], "msg": err["msg"]} for err in e.errors()]
        return templates.TemplateResponse(
            request=request,
            name="sections/login.html",
            context={"errors": errors},
        )

    user = await user_repo.get_by_email(form.email)
    if not user or not verify_password(form.password, user.password_hash):
        errors = [{"field": "email", "msg": "Email o contraseña incorrectos"}]
        return templates.TemplateResponse(
            request=request,
            name="sections/login.html",
            context={"errors": errors},
        )

    # Rotación de sesión: evita session fixation
    row = await db.fetchrow(
        "SELECT fn_obtener_o_crear_sesion(NULL::uuid) AS id",
    )
    new_session_id = str(row["id"])
    request.state.session_id = new_session_id
    await user_repo.link_to_session(user.id_usuario, new_session_id)
    return await servir_perfil(request, new_session_id, user_repo)


@router.post("/auth/register", response_class=HTMLResponse)
async def auth_register(
    request: Request,
    session_id: str = Depends(get_session),
    user_repo: UserRepo = Depends(get_user_repo),
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    try:
        form = RegisterForm(
            nombre=nombre, email=email,
            password=password, confirm_password=confirm_password,
        )
    except ValidationError as e:
        errors = [{"field": err["loc"][0], "msg": err["msg"]} for err in e.errors()]
        return templates.TemplateResponse(
            request=request,
            name="sections/register.html",
            context={"errors": errors},
        )

    existing = await user_repo.get_by_email(form.email)
    if existing:
        errors = [{"field": "email", "msg": "Este email ya está registrado"}]
        return templates.TemplateResponse(
            request=request,
            name="sections/register.html",
            context={"errors": errors},
        )

    password_hash = hash_password(form.password)
    await user_repo.create(session_id, form.nombre, form.email, password_hash)

    return await servir_perfil(request, session_id, user_repo)


@router.post("/auth/logout", response_class=HTMLResponse)
async def auth_logout(
    request: Request,
    session_id: str = Depends(get_session),
    user_repo: UserRepo = Depends(get_user_repo),
):
    await user_repo.unlink_session(session_id)
    request.state.session_id = ""
    resp = templates.TemplateResponse(
        request=request,
        name="sections/perfil.html",
        context={"user": None},
    )
    resp.delete_cookie(
        key="session_id",
        path="/",
    )
    return resp
