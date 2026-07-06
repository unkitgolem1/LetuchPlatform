"""Shared fixtures for all benchmarks — builds a real-ish FastAPI app with mocked DB."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from pathlib import Path

from routes import router
from routes.deps import get_db, ensure_session
from database import Database
from conftest import fake_record

BASE_DIR = Path(__file__).resolve().parent.parent.parent


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


async def session_middleware(request: Request, call_next):
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


@pytest.fixture(scope="session")
def app():
    os.environ["VERCEL"] = "false"

    mock_db = MagicMock(spec=Database)
    mock_db.fetchrow = AsyncMock(return_value=None)
    mock_db.fetch = AsyncMock(return_value=[])
    mock_db.execute = AsyncMock(return_value="OK")

    trans_conn = MagicMock()
    trans_conn.fetchrow = AsyncMock(return_value=fake_record({"id_pedido": "order-1", "created_at": None}))
    trans_conn.fetch = AsyncMock(return_value=[])
    trans_conn.execute = AsyncMock(return_value="OK")

    trans_cm = MagicMock()
    trans_cm.__aenter__ = AsyncMock(return_value=trans_conn)
    trans_cm.__aexit__ = AsyncMock(return_value=None)
    mock_db.transaction = AsyncMock(return_value=trans_cm)

    application = FastAPI()

    async def mock_ensure_session(request: Request):
        request.state.session_id = "bench-session-uuid-00000000"

    async def mock_get_db():
        return mock_db

    application.dependency_overrides[ensure_session] = mock_ensure_session
    application.dependency_overrides[get_db] = mock_get_db

    application.middleware("http")(security_headers_middleware)
    application.middleware("http")(session_middleware)

    application.include_router(router)

    static_dir = BASE_DIR / "static"
    if static_dir.exists():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return application, mock_db


@pytest.fixture(scope="session")
def client(app):
    application, _ = app
    with TestClient(application) as c:
        yield c
