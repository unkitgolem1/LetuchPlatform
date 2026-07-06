import os
import sys
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from routes import router
from database import Database
from exceptions import NotFoundError, CartEmptyError, InvalidCredentialsError, EmailAlreadyRegisteredError

load_dotenv()  # Carga .env si existe (no rompe si no está)


async def _async_startup():
    """Coroutine tasks de inicialización concurrente via gather."""
    tasks = []
    # ── Placeholder: aquí se añaden tareas async de arranque ──
    # tasks.append(init_db_connection())
    # tasks.append(warm_product_cache())
    if tasks:
        await asyncio.gather(*tasks)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database()
    try:
        await db.connect(os.getenv("DATABASE_URL"))
        app.state.db = db
    except Exception as exc:
        print(f"[lifespan] DB no disponible ({exc}). La app corre sin BD.")
        app.state.db = None
    await _async_startup()
    yield
    if app.state.db:
        await db.disconnect()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        content="<h1>404 — No encontrado</h1><p>El recurso solicitado no existe.</p>",
        status_code=404,
    )


@app.exception_handler(CartEmptyError)
async def cart_empty_handler(request: Request, exc: CartEmptyError):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        content=f"<p>{exc.args[0] if exc.args else 'Carrito vacío'}</p>",
        status_code=400,
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/auth/login", status_code=303)


@app.exception_handler(EmailAlreadyRegisteredError)
async def email_registered_handler(request: Request, exc: EmailAlreadyRegisteredError):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/auth/register", status_code=303)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://*.supabase.co; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """Fija la cookie session_id sobre la respuesta real (post-handler)."""
    response = await call_next(request)
    session_id = getattr(request.state, "session_id", None)
    if session_id:
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=os.getenv("VERCEL", "false").lower() == "true",
            samesite="lax",
            max_age=86400 * 30,
            path="/",
        )
    return response


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(router)
