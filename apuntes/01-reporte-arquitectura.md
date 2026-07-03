# Reporte de Arquitectura — LetuchWebSite

## 1. Rutas y Funciones (FastAPI)

### `src/main.py`
| Línea | Función / Elemento | Propósito |
|-------|-------------------|-----------|
| 11–18 | `_async_startup()` | Tareas de inicialización concurrente (lifespan). Aquí se inyectan conexiones a DB, warm caches, etc. |
| 27 | `app = FastAPI(lifespan=lifespan)` | Instancia principal de la app. |
| 28 | `app.mount("/static", ...)` | Sirve archivos estáticos. |
| 29 | `app.include_router(router)` | Importa las rutas desde `routes.py`. |

### `src/routes.py`
| Línea | Ruta | Función | Método | Respuesta | Template | Contexto actual |
|-------|------|---------|--------|-----------|----------|----------------|
| 62–67 | `/` | `servir_template` | GET | HTML | `index.html` | — |
| 70–81 | `/section/inicio` | `servir_fragmento_html_inicio` | GET | HTML (fragmento) | `sections/inicio.html` | `section_title`, `section_desc`, `productos` (lista vacía) |
| 84–95 | `/api/productos/{categoria}` | `productos_por_categoria` | GET | HTML (fragmento) | `sections/fragmento_card.html` | `productos`, `categoria` |
| 98–103 | `/section/servicios` | `servir_fragmento_html_servicio` | GET | HTML (fragmento) | `sections/servicios.html` | — |
| 106–111 | `/section/contacto` | `servir_fragmento_html_contacto` | GET | HTML (fragmento) | `sections/contacto.html` | — |
| 114–119 | `/perfil` | `servir_perfil` | GET | HTML (fragmento) | `sections/perfil.html` | — (template espera `user`) |
| 122–128 | `/carrito` | `servir_carrito` | GET | HTML (fragmento) | `sections/carrito.html` | `items: []`, `total: 0` |

### Rutas referenciadas en templates pero NO implementadas
| Ruta | Método | Origen (template) | Propósito |
|------|--------|-------------------|-----------|
| `/carrito_db` | POST | `fragmento_card.html`, `carrito.html` | Agregar/restar/quitar items del carrito. |
| `/perfil` | GET | — | Ya existe, pero sin DB. |
| `/carrito` | GET | — | Ya existe, pero sin DB. |

---

## 2. Puntos de Inyección para DB / Repos

### Dependencias actuales

| Función | Inyecta | Inyectado en |
|---------|---------|-------------|
| `get_db` | `Database` | todas las demás dependencias |
| `get_session_id` | `str` (session_id UUID) | `/perfil`, `/carrito`, `POST /carrito_db` |
| `get_product_repo` | `ProductRepo` | `/api/productos/{categoria}` |
| `get_user_repo` | `UserRepo` | `/perfil` |
| `get_cart_repo` | `CartRepo` | `/carrito`, `POST /carrito_db` |

### Flujo de session_id

```
GET /carrito
  → request.cookies["session_id"] (o None)
  → fn_obtener_o_crear_sesion($1::uuid)  — PL/pgSQL en DB
  → response.set_cookie("session_id", …, httponly, secure)
  → return session_id (str)
```

### Repos inyectados

| Ruta | Función | Dependencias |
|------|---------|-------------|
| `GET /` | `servir_template` | — |
| `GET /section/inicio` | `inicio` | — |
| `GET /api/productos/{categoria}` | `productos_por_categoria` | `ProductRepo` |
| `GET /section/servicios` | `servicio` | — |
| `GET /section/contacto` | `contacto` | — |
| `GET /perfil` | `servir_perfil` | `get_session_id`, `UserRepo` |
| `GET /carrito` | `servir_carrito` | `get_session_id`, `CartRepo` |
| `POST /carrito_db` | `carrito_post` | `get_session_id`, `CartRepo`, `OrderRepo` |
| `GET /mis-pedidos` | `servir_mis_pedidos` | `get_session_id`, `OrderRepo` |
| `GET /section/pedido/{id}` | `servir_pedido` | `get_session_id`, `OrderRepo` |

---

## 3. Modelos Pydantic (`src/models.py`)

### 3.1 User (público, sin password)

```python
class User(BaseModel):
    id_usuario: str
    id_sesion: str
    nombre: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = ""
    created_at: Optional[datetime] = None

    @property
    def miembros_desde(self) -> Optional[str]:
        if self.created_at:
            return self.created_at.strftime("%d/%m/%Y")
        return None
```

### 3.2 UserWithPsw (solo para repositorio, hereda User)

```python
class UserWithPsw(User):
    password_hash: str
```

Nunca se expone en templates. Solo `UserRepo.get_with_psw_by_session()` lo retorna.

### 3.3 Sesion

```python
class Sesion(BaseModel):
    id: str
    created_at: datetime
    expires_at: datetime
```

### 3.4 CarritoItem

```python
class CarritoItem(BaseModel):
    id_item: str
    id_carrito: str
    id_producto: int
    titulo: str
    descripcion: str = ""
    imagen: str = ""
    precio_unitario: Decimal
    cantidad: int
    subtotal: Decimal
```

### 3.5 Carrito

```python
class Carrito(BaseModel):
    id_carrito: str
    id_sesion: str
    estado: str = "activo"
    items: list[CarritoItem] = []

    @property
    def total(self) -> Decimal:
        return sum(i.subtotal for i in self.items)
```

---

## 4. Mapeo Tablas → Modelos → Repos

| Tabla DB | Modelo Python | Repo |
|----------|-------------|------|
| `productos` | (dict inline en repo) | `ProductRepo` |
| `sesiones` | `Sesion` | — (vía `fn_obtener_o_crear_sesion`) |
| `usuarios` | `User` / `UserWithPsw` | `UserRepo` |
| `carritos` | `Carrito` | `CartRepo` |
| `items_carrito` | `CarritoItem` | `CartRepo` |
| `pedidos` | `Pedido` | `OrderRepo` |
| `pedido_items` | `PedidoItem` | `OrderRepo` |

### Relaciones
```
sesiones 1──1 usuarios (id_sesion FK UNIQUE)
sesiones 1──N carritos (id_sesion FK)
carritos 1──N items_carrito (id_carrito FK)
productos 1──N items_carrito (id_producto FK)
sesiones 1──N pedidos (id_sesion FK)
pedidos 1──N pedido_items (id_pedido FK)
productos 1──N pedido_items (id_producto FK)
```

---

## 5. Estado Actual

- **DB**: PostgreSQL via Supabase, SSL requerido
- **Auth**: `session_id` UUID en cookie httponly/secure/samesite. No JWT.
- **Fallback**: eliminado. Sin DB → error 500.
- **Modelos**: `User`, `UserWithPsw(User)`, `Carrito`, `CarritoItem`, `Pedido`, `PedidoItem`, `Sesion`
- **Repos**: `ProductRepo`, `CartRepo`, `UserRepo`, `OrderRepo`
- **Endpoints**: 8 GET + 1 POST (`/carrito_db`, `/mis-pedidos`, `/section/pedido/{id}`)
- **SQL schema**: `sql/supabase_schema.sql` (sesiones, usuarios, carritos, items_carrito, pedidos, pedido_items + vistas + funciones PL/pgSQL)
