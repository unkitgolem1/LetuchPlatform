"""Static pages: home, sections, robots.txt, sitemap.xml."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from .deps import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def servir_template(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/section/inicio", response_class=HTMLResponse)
async def inicio(request: Request):
    return templates.TemplateResponse(request=request, name="sections/inicio.html")


@router.get("/section/servicios", response_class=HTMLResponse)
async def servicio(request: Request):
    return templates.TemplateResponse(request=request, name="sections/servicios.html")


@router.get("/section/contacto", response_class=HTMLResponse)
async def contacto(request: Request):
    return templates.TemplateResponse(request=request, name="sections/contacto.html")


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
