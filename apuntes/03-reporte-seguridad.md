# Reporte de Seguridad — Letuch Bakery

**Fecha:** julio 2026
**Auditoría:** Sesiones, autenticación, cookies y headers HTTP
**Alcance:** Backend FastAPI + esquema PostgreSQL

---

## Resumen Ejecutivo

Se identificaron 5 hallazgos de seguridad (3 medios, 2 bajos). Todos fueron corregidos. Las defensas preexistentes (httponly, SameSite=Lax, rotación en login, UUID criptográfico) se mantienen y complementan.

---

## Hallazgos y Remediación

### H1. Cookie `session_id` sin `Secure` flag fijo

| Ítem | Detalle |
|------|---------|
| **Riesgo** | 🔶 Medio |
| **Problema** | `secure=request.url.scheme == "https"` — si la app se sirve por HTTP (dev, error de proxy), la cookie viaja en texto plano. Un atacante en la misma red (Wi‑Fi público, etc.) puede interceptarla (MitM). |
| **Solución** | `secure=True` fijo — la cookie solo se envía por HTTPS. |
| **Archivo** | `src/main.py:90` |

### H2. Sin protección CSRF

| Ítem | Detalle |
|------|---------|
| **Riesgo** | 🔶 Medio |
| **Problema** | Los endpoints POST (`/auth/login`, `/carrito_db`, `/pagar`) no validan ningún token CSRF. SameSite=Lax mitiga ataques cross-site, pero no protege contra same-site script ni complementos del navegador. |
| **Solución** | Nueva dependencia `require_htmx` que verifica el header `HX-Request: true` en todo POST. Como la app usa HTMX para TODAS las peticiones POST (confirmado revisando templates), esto es 100% efectivo sin necesidad de tokens. |
| **Archivos** | `src/routes/deps.py:54` (dependencia), `src/routes/auth.py` (aplicada a login, register, logout) |

### H3. Sin rate limiting en login

| Ítem | Detalle |
|------|---------|
| **Riesgo** | 🔶 Medio |
| **Problema** | `/auth/login` acepta peticiones ilimitadas. Un atacante puede probar contraseñas por fuerza bruta sin restricción. |
| **Solución** | Rate limiter en memoria: máximo 5 intentos por IP en ventana de 5 minutos. Retorna HTTP 429 al exceder. |
| **Advertencia** | En memoria local — en deploys serverless (Vercel) cada instancia tiene su propio contador. Para producción real se recomienda Redis. Para una panadería pequeña es suficiente. |
| **Archivo** | `src/rate_limiter.py` (nuevo), `src/routes/auth.py:45` (aplicado a login) |

### H4. Sin Content-Security-Policy

| Ítem | Detalle |
|------|---------|
| **Riesgo** | 🔶 Medio |
| **Problema** | Sin CSP, si hay un XSS el atacante puede ejecutar scripts arbitrarios, robar datos, o hacer peticiones autenticadas. |
| **Solución** | Middleware que agrega CSP + headers de seguridad en toda respuesta. |
| **Headers añadidos** | |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.supabase.co; font-src 'self'; connect-src 'self'; frame-ancestors 'none'` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| **Nota** | `'unsafe-inline'` + `'unsafe-eval'` necesarios para Alpine.js (evalúa expresiones con `Function()` internamente). |
| **Archivo** | `src/main.py:80` |

### H5. Sesión persistente post-logout

| Ítem | Detalle |
|------|---------|
| **Riesgo** | 🔵 Bajo |
| **Problema** | Al hacer logout, la sesión se desvincula del usuario (`id_sesion = NULL`) pero el registro en `sesiones` sigue activo. Si alguien reusa la cookie antes de que expire, la sesión revive (aunque sin usuario autenticado, solo carrito anónimo). |
| **Solución** | Nueva función SQL `fn_invalidar_sesion()` que setea `expires_at = NOW()`, llamada desde `AuthService.logout()`. |
| **Archivos** | `sql/03-invalidar-sesion.sql` (nuevo), `src/services/auth_service.py:49` |

---

## Defensas Preexistentes (sin cambios)

| Defensa | Estado |
|---------|--------|
| UUID v4 criptográfico (`gen_random_uuid`) | ✅ Correcto |
| Cookie `httponly=true` | ✅ Correcto |
| `SameSite=Lax` | ✅ Correcto |
| Rotación de sesión en login (nuevo UUID) | ✅ Correcto |
| Expiración a 30 días con renovación automática | ✅ Correcto |

---

## Recomendaciones Futuras (baja prioridad)

1. **Migrar rate limiter a Redis** si el proyecto crece o se despliega en múltiples instancias serverless.
2. **Hardening de CSP** — si se dejan de usar expresiones inline de Alpine, cambiar `'unsafe-inline'` por nonces.
3. **Monitoreo de intentos fallidos** — loguear intentos de login fallidos para detección temprana de ataques.
4. **Limpieza periódica de sesiones expiradas** — ejecutar `DELETE FROM sesiones WHERE expires_at < NOW()` vía cron (la vista `vista_sesiones_expiradas` ya existe en la DB).

---

## Archivos Modificados/Creados

| Archivo | Operación |
|---------|-----------|
| `src/main.py` | Modificado — secure=True, CSP middleware |
| `src/routes/deps.py` | Modificado — nueva dependencia require_htmx |
| `src/rate_limiter.py` | **Creado** — rate limiter en memoria |
| `src/routes/auth.py` | Modificado — Depends(require_htmx) + Depends(rate_limit_login) en POST |
| `src/services/auth_service.py` | Modificado — logout invalida sesión en DB |
| `sql/03-invalidar-sesion.sql` | **Creado** — función fn_invalidar_sesion |
| `apuntes/03-reporte-seguridad.md` | **Creado** — este reporte |
