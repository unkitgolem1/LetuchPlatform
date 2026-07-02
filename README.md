# LetuchWebSite

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI (Python 3.13+) |
| Templates | Jinja2 |
| CSS | Tailwind CSS v3 (CDN Play) |
| Interactividad | HTMX 2.0 |
| Tipografía títulos | Archivo Black (Typekit) |
| Tipografía cuerpo | Satoshi (Fontshare) |

---

## Rutas del Backend

Cada ruta devuelve HTML (parcial o completo). Las rutas `/section/*` devuelven fragmentos que HTMX inyecta en `#content-area`. Las rutas `/perfil` y `/carrito` devuelven fragmentos para el modal.

### GET `/`
Página principal completa (`index.html`). Sin variables de contexto.

### GET `/section/inicio`
Fragmento de inicio. Espera estas variables en el contexto Jinja:

| Variable | Tipo | Descripción |
|---|---|---|
| `section_title` | `str` | Título de la sección |
| `section_desc` | `str` | Descripción de la sección |
| `documentos` | `list[dict]` | Lista de documentos |

### GET `/section/servicios`
Fragmento de servicios. Mismas variables que `/section/inicio`.

### GET `/section/contacto`
Fragmento de contacto. Mismas variables que `/section/inicio`.

### GET `/perfil`
Fragmento para el modal de perfil. Espera:

| Variable | Tipo | Descripción |
|---|---|---|
| `user` | `dict` | Datos del usuario |

Estructura de `user`:
```python
user = {
    "nombre": str,
    "email": str,
    "avatar": str | None,   # URL de imagen
    "miembros_desde": str,  # ej. "Enero 2026"
}
```

### GET `/carrito`
Fragmento para el modal del carrito. Espera:

| Variable | Tipo | Descripción |
|---|---|---|
| `items` | `list[dict]` | Lista de items en el carrito |
| `total` | `float` | Monto total |

Estructura de cada item en `items`:
```python
{
    "id": int | str,
    "titulo": str,
    "descripcion": str,
    "imagen": str | None,
    "precio": float,
    "cantidad": int,
}
```

---

## Estructura de `documentos`

Todas las secciones (`/section/*`) reciben una lista `documentos`. Cada documento:

```python
{
    "titulo": str,          # Título del documento
    "descripcion": str,     # Descripción / body
    "imagen": str | None,   # URL de imagen (opcional)
}
```

Si `imagen` es `None` o está vacía, el template muestra un placeholder (círculo con número).

---

## Modales (Perfil y Carrito)

Los botones de perfil y carrito en el navbar usan HTMX para cargar contenido en un modal global:

```
[Botón perfil] ──hx-get="/perfil"──→ #modal-body ──→ openModal()
[Botón carrito] ──hx-get="/carrito"──→ #modal-body ──→ openModal()
```

El modal se cierra con:
- Botón ✕
- Click fuera del modal (backdrop)
- Tecla Escape

Controlado por las funciones JS `openModal()` y `closeModal()` definidas en `base.html`.

---

## Templates

| Archivo | Rol |
|---|---|
| `base.html` | Layout base (head, modales, JS global) |
| `index.html` | Página principal (hero, navbar, content-area, footer) |
| `sections/inicio.html` | Fragmento grid de documentos |
| `sections/servicios.html` | Fragmento lista de documentos |
| `sections/contacto.html` | Fragmento contacto documento |

Cada section template itera `{% for doc in documentos %}` y usa `doc.titulo`, `doc.descripcion`, `doc.imagen`.

---

## Diseño visual

- **Paleta**: `#57984F` (brand), `#1A1D1A` (dark), `#2E669A` (blue-accent), `#F0EDE5` (false-white), `#FAF9F5` (lighter)
- **Contenedor**: `.phi-container` con padding progresivo (1rem → 5rem) y `max-width: 1440px` en ultra-wide
- **Neumorphism**: `.sunken-neumo` con sombras inset para efecto hundido
- **Hero**: Fondo brand con plantas SVG animadas en la base, letras con hover jump
