# Manual de Seguridad — LetuchWebSite

FastAPI ya trae varias protecciones integradas. Esto es lo que hay que agregar/configurar para un sitio en producción.

---

## Índice

1. [Headers de seguridad (middleware)](#1-headers-de-seguridad)
2. [CSRF Protection](#2-csrf-protection)
3. [Cookie `session_id` segura](#3-cookie-session_id-segura)
4. [Rate Limiting en endpoints POST](#4-rate-limiting)
5. [Sanitización de input](#5-sanitización-de-input)
6. [Trusted Hosts](#6-trusted-hosts)
7. [CORS (si aplica)](#7-cors)
8. [Checklist de producción](#8-checklist-de-producción)

---

## 1. Headers de seguridad

Agregar un middleware que inyecte headers en toda respuesta.

### Dependencia
```bash
pip install secure
# o manual con Starlette middleware
```

### Implementación en `main.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app = FastAPI(lifespan=lifespan)
app.add_middleware(SecurityHeadersMiddleware)
```

### Qué hace cada header

| Header | Valor | Efecto |
|--------|-------|--------|
| `X-Content-Type-Options` | `nosniff` | Evita MIME sniffing |
| `X-Frame-Options` | `DENY` | Evita clickjacking (no se puede embeber en iframe) |
| `X-XSS-Protection` | `1; mode=block` | Bloquea reflejo XSS (legacy browsers) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controla qué se envía en Referer |
| `Permissions-Policy` | `geolocation=(), ...` | Desactiva APIs de navegador no usadas |

---

## 2. CSRF Protection

htmx hace peticiones same-origin, pero un endpoint POST sin CSRF es vulnerable si alguien logra ejecutar un formulario externo.

### Dependencia
```bash
pip install fastapi-csrf-protect
```

### Implementación

```python
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class CsrfSettings(BaseModel):
    secret_key: str = "un-secreto-muy-largo-cambiame-en-produccion"

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

app = FastAPI()
app.add_middleware(CsrfProtect)
```

### Alternativa ligera (sin dependencias extra)

FastAPI/Starlette no tiene CSRF middleware nativo. Puedes implementar un chequeo manual con `Origin` + `Referer`:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SimpleCsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            origin = request.headers.get("origin", "")
            host = request.headers.get("host", "")

            if not origin and not request.headers.get("referer", ""):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF check failed: missing origin/referer"},
                )

            # Verificar que origin/referer coincide con nuestro host
            allowed = False
            if origin and host in origin:
                allowed = True
            if not allowed:
                ref = request.headers.get("referer", "")
                if ref and host in ref:
                    allowed = True

            if not allowed:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF check failed: invalid origin"},
                )

        return await call_next(request)
```

---

## 3. Cookie `session_id` segura

Para identificar carrito de guest sin login.

### Implementación

```python
import uuid
from datetime import datetime, timedelta
from fastapi import Request, Response

SESSION_COOKIE_NAME = "session_id"
SESSION_MAX_AGE = 86400 * 7  # 7 días

def get_or_create_session(request: Request, response: Response) -> str:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,      # no accesible desde JS
            secure=True,        # solo HTTPS (en producción)
            samesite="lax",     # protege contra CSRF básico
            max_age=SESSION_MAX_AGE,
            path="/",
        )
    return session_id
```

### Flags de cookie explicados

| Flag | Valor | Por qué |
|------|-------|---------|
| `httponly=True` | No accesible via `document.cookie` | Evita robo por XSS |
| `secure=True` | Solo se envía por HTTPS | Nunca en texto plano |
| `samesite="lax"` | No se envía en requests cross-site POST | Protege contra CSRF |
| `max_age=604800` | Expira en 7 días | Sesión persistente |

**⚠️ En desarrollo local (localhost), `secure=True` impide que la cookie se guarde. Usar `secure=False` en dev o solo activarlo con una variable de entorno.**

```python
import os
SECURE_COOKIE = os.getenv("ENV", "development") == "production"
```

---

## 4. Rate Limiting

Proteger endpoints POST contra abuso (ej. agregar 1000 items al carrito en 1s).

### Dependencia
```bash
pip install slowapi
```

### Implementación en `main.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Decorar endpoints POST en `routes.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/carrito_db")
@limiter.limit("10/minute")  # máx 10 requests por minuto por IP
async def carrito_db_post(request: Request):
    ...
```

Para desarrollo puedes desactivarlo o subir el límite.

---

## 5. Sanitización de input

### Lo que FastAPI ya hace
- Pydantic valida tipos automáticamente (int, str, Decimal, etc.)
- Jinja2 escapa HTML con `{{ variable }}` (usa `|safe` solo si confías el contenido)

### Lo que hay que hacer manual

```python
from markupsafe import escape

# Si por alguna razón necesitas escapar fuera de Jinja2
nombre_limpio = escape(user_input)

# Para evitar XSS en atributos HTML generados dinámicamente
# siempre usar comillas y nunca concatenar crudo
```

### SQL Injection (cuando llegue la DB)

Nunca concatenar strings en queries SQL. Usar **parametrización**:

```python
# ❌ PELIGROSO
query = f"SELECT * FROM productos WHERE id = {id}"

# ✅ SEGURO (asyncpg)
row = await conn.fetchrow("SELECT * FROM productos WHERE id = $1", id)

# ✅ SEGURO (psycopg)
cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
```

---

## 6. Trusted Hosts

Evita que alguien apunte un DNS falso a tu servidor.

### Implementación en `main.py`

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "letuch.com",
        "www.letuch.com",
        "localhost",
        "127.0.0.1",
    ],
)
```

### CORS (Cross-Origin Resource Sharing)

Solo necesario si recibes requests de otros orígenes. Para este proyecto (todo same-origin), no hace falta. Si en el futuro hay API pública, agregar:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://letuch.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 7. HTTPS

Esto es del deploy, no del código. Pero el código debe estar listo:

- `secure=True` en cookies (condicional según entorno)
- Redirigir HTTP → HTTPS a nivel de reverse proxy (Nginx/Caddy/Traefik)

### Ejemplo Caddy (recomendado para producción)
```caddyfile
letuch.com {
    reverse_proxy localhost:8000
}
```
Caddy maneja SSL automáticamente (Let's Encrypt).

---

## 8. Checklist de producción

- [ ] `SECURE_COOKIE = True` (en producción)
- [ ] `secret_key` larga y rotada (no hardcodeada, usar `os.getenv`)
- [ ] TrustedHostMiddleware con los dominios reales
- [ ] Rate limiting en todos los endpoints POST
- [ ] CSRF middleware activo
- [ ] SecurityHeadersMiddleware activo
- [ ] HTTPS en el reverse proxy
- [ ] Logging de errores (no exponer stack traces al cliente)
- [ ] `DEBUG = False` en FastAPI

### Configuración final de `main.py`

```python
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from routes import router
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.csrf import SimpleCsrfMiddleware

ENV = os.getenv("ENV", "development")
SECURE_COOKIE = ENV == "production"

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan, debug=(ENV != "production"))
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SimpleCsrfMiddleware)
if ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["letuch.com", "www.letuch.com"],
    )

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
```

---

## Dependencias totales para seguridad

```bash
pip install slowapi markupsafe
# fastapi-csrf-protect es opcional (ver sección 2)
```

Eso es todo. FastAPI + estos middlewares cubren OWASP Top 10 para un sitio de este tipo.
