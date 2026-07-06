"""Shared utilities — body parsing, error formatting, SQL helpers."""

from fastapi import Request
from pydantic import ValidationError


async def parse_request_body(request: Request) -> dict:
    """Parse request body from either JSON or form data."""
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        try:
            return await request.json()
        except Exception:
            return {}
    form = await request.form()
    return dict(form)


def format_validation_errors(err: ValidationError) -> list[dict]:
    """Convert Pydantic ValidationError to template-friendly error list."""
    return [
        {"field": err["loc"][0] if err["loc"] else "", "msg": err["msg"]}
        for err in err.errors()
    ]


def cart_scope_subquery(session_alias: str = "$1") -> str:
    """Reusable subquery fragment scoping operations to the active cart."""
    return (
        f"id_carrito IN ("
        f"  SELECT id_carrito FROM carritos"
        f"  WHERE id_sesion = {session_alias}::uuid AND estado = 'activo'"
        f")"
    )
