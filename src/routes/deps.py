"""Shared dependencies, utilities, and templates for all sub-routers."""

from typing import Optional
from fastapi import Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pathlib import Path
from starlette.status import HTTP_403_FORBIDDEN

from database import Database
from models import User
from repos.product_repo import ProductRepo
from repos.cart_repo import CartRepo
from repos.user_repo import UserRepo
from repos.order_repo import OrderRepo
from services.auth_service import AuthService
from services.cart_service import CartService
from services.order_service import OrderService


BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "static" / "templates"))


def get_db(request: Request) -> Database:
    return request.app.state.db


async def ensure_session(
    request: Request,
    db: Database = Depends(get_db),
) -> None:
    """Router-level dependency: resolves session_id into request.state."""
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


async def require_htmx(request: Request):
    if request.method == "POST" and not request.headers.get("HX-Request"):
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="CSRF: falta header HX-Request")


def get_product_repo(db: Database = Depends(get_db)) -> ProductRepo:
    return ProductRepo(db)


def get_user_repo(db: Database = Depends(get_db)) -> UserRepo:
    return UserRepo(db)


def get_cart_repo(db: Database = Depends(get_db)) -> CartRepo:
    return CartRepo(db)


def get_order_repo(db: Database = Depends(get_db)) -> OrderRepo:
    return OrderRepo(db)


def get_auth_service(
    user_repo: UserRepo = Depends(get_user_repo),
    db: Database = Depends(get_db),
) -> AuthService:
    return AuthService(user_repo, db)


def get_cart_service(
    cart_repo: CartRepo = Depends(get_cart_repo),
    product_repo: ProductRepo = Depends(get_product_repo),
) -> CartService:
    return CartService(cart_repo, product_repo)


def get_order_service(
    order_repo: OrderRepo = Depends(get_order_repo),
) -> OrderService:
    return OrderService(order_repo)


async def get_current_user(
    session_id: str = Depends(get_session),
    repo: UserRepo = Depends(get_user_repo),
) -> Optional[User]:
    return await repo.get_by_session(session_id)


async def login_required(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
) -> Optional[User]:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Se necesita iniciar sesión")
    return current_user


async def servir_perfil_response(
    request: Request,
    session_id: str,
    repo: UserRepo,
):
    """Render the profile template — reused by profile route and auth handlers."""
    user = await repo.get_by_session(session_id)
    return templates.TemplateResponse(
        request=request,
        name="sections/perfil.html",
        context={"user": user},
    )
