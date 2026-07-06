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
            secure=request.url.scheme == "https",
            samesite="lax",
            max_age=86400 * 30,
            path="/",
        )
    return response


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(router)
