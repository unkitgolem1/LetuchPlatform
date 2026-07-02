from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()

router.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "static" / "templates"))


@router.get("/", response_class=HTMLResponse)
async def servir_template(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@router.get("/section/inicio", response_class=HTMLResponse)
async def servir_fragmento_html_inicio(request: Request):
    lista_productos = [
        {
            "id": "1", 
            "titulo": "Chocolatina", 
            "descripcion": "Delicioso pan de chocolate artesanal.", 
            "imagen": "", 
            "precio": 52,
            "cantidad": 5
        },
    ]
    return templates.TemplateResponse(
        request=request,
        name="/sections/inicio.html",
        context={
            "section_title": "Vitrina",
            "section_desc": "Explora nuestros productos:",
            "productos": lista_productos,
        },
    )


@router.get("/section/servicios", response_class=HTMLResponse)
async def servir_fragmento_html_servicio(request: Request):
 
    documentos=[
            {
                "titulo":"Servicio de Vitrina",
                "imagen":"/static/images/caption.webp",
                "descripcion":"Una muestra de nuestro pan fresco disponible en nuestras tiendas",               
            },
            {
                "titulo":"Servicio de Surtido a cafeterias",
                "imagen":"/static/images/721266118_18538905730073817_2825081271361550579_n.jpg",
                "descripcion":"Surtimos pan frezco y artesanal apartir de las 8:00AM",               
            },
            {
                "titulo":"Larder & Kitchen",
                "imagen":"/static/images/borbon.jpg",
                "descripcion":"Nacimos para el café, pero nuestra cocina de firma te hará volver.",               
            },
            {
                "titulo":"Culto al Café & Bebidas de Especialidad",
                "imagen":"/static/images/Bebida.jpg",
                "descripcion":"una carta de bebidas frías y calientes diseñada para complementar nuestra cocina",               
            }
    ]

    return templates.TemplateResponse(
        request=request,
        name="/sections/servicios.html",
        context={
            "section_title": "Servicios",
            "section_desc": "Soluciones y servicios diseñados para la comodidad y crecimiento del negocio.",
            "documentos": documentos,
        },
    )


@router.get("/section/contacto", response_class=HTMLResponse)
async def servir_fragmento_html_contacto(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/contacto.html",
        context={
            "section_title": "Contacto",
            "section_desc": "Hablemos de tu próximo proyecto.",
            "documentos": [],
        },
    )


@router.get("/perfil", response_class=HTMLResponse)
async def servir_perfil(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/perfil.html",
    )


@router.get("/carrito", response_class=HTMLResponse)
async def servir_carrito(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="sections/carrito.html",
        context={"items": [], "total": 0}
    )
