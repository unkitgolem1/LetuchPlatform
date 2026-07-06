"""Authentication routes: login, register, logout."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from .deps import (
    templates,
    get_session,
    get_user_repo,
    get_auth_service,
    require_htmx,
    servir_perfil_response,
)
from forms import LoginForm, RegisterForm
from utils import format_validation_errors
from exceptions import InvalidCredentialsError, EmailAlreadyRegisteredError
from rate_limiter import rate_limit_login

router = APIRouter()


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
    auth_service=Depends(get_auth_service),
    user_repo=Depends(get_user_repo),
    email: str = Form(...),
    password: str = Form(...),
    _c=Depends(require_htmx),
    _r=Depends(rate_limit_login),
):
    try:
        form = LoginForm(email=email, password=password)
    except ValidationError as e:
        return templates.TemplateResponse(
            request=request,
            name="sections/login.html",
            context={"errors": format_validation_errors(e)},
        )

    try:
        user, new_session_id = await auth_service.login(
            form.email, form.password, session_id
        )
    except InvalidCredentialsError:
        errors = [{"field": "email", "msg": "Email o contraseña incorrectos"}]
        return templates.TemplateResponse(
            request=request,
            name="sections/login.html",
            context={"errors": errors},
        )

    request.state.session_id = new_session_id
    return await servir_perfil_response(request, new_session_id, user_repo)


@router.post("/auth/register", response_class=HTMLResponse)
async def auth_register(
    request: Request,
    session_id: str = Depends(get_session),
    auth_service=Depends(get_auth_service),
    user_repo=Depends(get_user_repo),
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    _c=Depends(require_htmx),
):
    try:
        form = RegisterForm(
            nombre=nombre,
            email=email,
            password=password,
            confirm_password=confirm_password,
        )
    except ValidationError as e:
        return templates.TemplateResponse(
            request=request,
            name="sections/register.html",
            context={"errors": format_validation_errors(e)},
        )

    try:
        await auth_service.register(
            session_id, form.nombre, form.email, form.password
        )
    except EmailAlreadyRegisteredError:
        errors = [{"field": "email", "msg": "Este email ya está registrado"}]
        return templates.TemplateResponse(
            request=request,
            name="sections/register.html",
            context={"errors": errors},
        )

    return await servir_perfil_response(request, session_id, user_repo)


@router.post("/auth/logout", response_class=HTMLResponse)
async def auth_logout(
    request: Request,
    session_id: str = Depends(get_session),
    auth_service=Depends(get_auth_service),
    _c=Depends(require_htmx),
):
    await auth_service.logout(session_id)
    request.state.session_id = ""
    resp = templates.TemplateResponse(
        request=request,
        name="sections/perfil.html",
        context={"user": None},
    )
    resp.delete_cookie(key="session_id", path="/")
    return resp
