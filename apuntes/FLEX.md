# 🚀 Letuch Bakery — Speedrun Results

Weno, hice benchmarks de mi página pa' que vean que no es puro CSS bonito.

## TL;DR — La página vuela 🦅

| Ruta | Tiempo | Tamaño |
|------|--------|--------|
| 🏠 Home | **1.3 ms** | 4.8 KB |
| 🔐 Login | **1.2 ms** — más rápido | 3.2 KB |
| 🛒 Carrito | **2.5 ms** | 5.1 KB |
| 🍞 Productos API | **1.6 ms** | 4.1 KB |
| 📄 Secciones | **~1.5 ms** | ~5 KB |
| 📦 JS/CSS | **~2 ms** | varios KB |
| 🛡️ Headers seguridad | +**280 bytes** por request | — |

## Throughput — ¿Aguanta el jale?

| Conexiones | RPS |
|------------|-----|
| 1 persona | **646 req/s** |
| 5 personas | **530 req/s** |
| 10 personas | **490 req/s** |

Diez morros jalando al mismo tiempo y responde en **~2 ms**. Sin pedos.

## Memoria — No se traga la RAM

```
Estado          MB     vs anterior
──────────────────────────────────
Al arrancar     65 MB  ─
10 requests     65.1   +0.1 MB
50 requests     65.3   +0.3 MB
100 requests    65.5   +0.5 MB
```

Cada request cuesta **~5 KB**. Navegar 10 páginas = **50 KB**. Menos que un .jpg.

## Mis números completos

```
Benchmark                      Tiempo     Contra el más rápido
───────────────────────────────────────────────────────────────
/login form                   1.2 ms     1.0x  ← este ganó
/register form                1.2 ms     1.02x
/home                         1.3 ms     1.09x
/inicio section               1.5 ms     1.30x
/servicios section            1.5 ms     1.31x
static CSS                    1.6 ms     1.32x
/perfil (invitado)            1.6 ms     1.33x
/perfil (logueado)            1.6 ms     1.36x
productos API                 1.6 ms     1.37x
/contacto section             1.6 ms     1.37x
htmx.js                       2.0 ms     1.65x
/carrito                      2.5 ms     2.12x  ← este fue el más lento (tiene queries)
```

## Stack

```
Python 3.13 + FastAPI + HTMX + Alpine.js + Tailwind
PostgreSQL (Supabase) — mockeado en benchmarks
```

---

# 🏆 Versus: Cómo se ve contra otros lenguajes

Ahora sí, lo que vinieron a ver. Busqué benchmarks públicos (TechEmpower, CodeArchaeology, Travis Luong) con la misma arquitectura: API JSON + PostgreSQL, mismas condiciones.

## JSON plano (sin base de datos)

*— Solo serializar un JSON y devolverlo. El CPU puro.*

| Framework | Lenguaje | Req/s | vs FastAPI |
|-----------|----------|------:|-----------:|
| ⚡ Gin | Go | **120,000** | 12x más rápido |
| ⚡ Fastify | Node.js | **~30,000** | 3x más rápido |
| 🟢 Express | Node.js | **~30,000** | 3x más rápido |
| ☕ Spring Boot (WebFlux) | Java | **~23,000** | 2.3x más rápido |
| 🐍 **FastAPI** | **Python** | **~10,000** | **1.0x ← esto es lo nuestro** |
| 💜 ASP.NET Core | C# | **~14,700** | 1.5x más rápido |
| ♦️ Ruby on Rails (YJIT) | Ruby | **~2,300** | 4.3x más lento |

## 1 consulta a PostgreSQL

*— El escenario más realista: un SELECT con parámetro.*

| Framework | Req/s | vs FastAPI |
|-----------|------:|-----------:|
| ⚡ Gin (Go) | **~18,000** | 3x más rápido |
| ☕ Spring Boot (Java) | **~14,200** | 2.4x más rápido |
| 🟢 Express (Node.js) | **~8,000** | 1.3x más rápido |
| 🐍 **FastAPI** | **~6,000** | **1.0x ← esto es lo nuestro** |
| ♦️ Rails (Ruby) | **~2,300** | 2.6x más lento |

> La diferencia se achica cuando hay base datos de por medio. El bottleneck ya no es el lenguaje, es la red.

## 20 consultas a PostgreSQL

*— Un endpoint culero que hace 20 queries. Duele en todos lados.*

| Framework | Req/s | vs FastAPI |
|-----------|------:|-----------:|
| ⚡ Gin (Go) | **~4,500** | 2.5x más rápido |
| 🟢 Express (Node.js) | **~2,200** | 1.2x más rápido |
| 🐍 **FastAPI** | **~1,800** | **1.0x** |
| ♦️ Rails (Ruby) | **~800** | 2.2x más lento |

> Con muchas queries async, FastAPI se acerca mucho a Node.js porque el cuello de botella es la red, no el CPU.

## Memoria RAM en idle

*— Cuando el server no está haciendo nada, solo respirando.*

| Framework | RAM idle | vs FastAPI |
|-----------|---------:|-----------:|
| ⚡ Gin (Go) | **~16 MB** | 6x **menos** RAM |
| 🐍 **FastAPI** | **~95 MB** | **1.0x** |
| 🟢 Express (Node.js) | **~83 MB** | ~igual |
| ♦️ Rails (Ruby) | **~125 MB** | 1.3x más |
| 💜 ASP.NET Core (C#) | **~137 MB** | 1.4x más |
| ☕ Spring Boot (Java) | **~310 MB** | 3.3x más |
| ☕ Spring Boot legacy | **~597 MB** | 6.3x más |

## RAM bajo carga (1000 conexiones)

| Framework | RAM bajo carga |
|-----------|--------------:|
| ⚡ Gin (Go) | **~112 MB** |
| 🐍 FastAPI | **~280 MB** |
| ☕ Spring Boot (Java) | **~480 MB** |

## Cold start (primera vez que arranca)

| Framework | Tiempo |
|-----------|-------|
| ⚡ Gin (Go) | **Instantáneo** (~5 ms) — binario compilado |
| 🟢 Express / Fastify (Node.js) | **~100-200 ms** |
| 🐍 **FastAPI** | **~500-1000 ms** |
| ♦️ Rails (Ruby) | **~2-3 seg** |
| ☕ Spring Boot (Java) | **~3-6 seg** |

---

## Moraleja

```
         ⚡ Go:   más rápido, menos RAM, más código que escribir
         🐍 Python/FastAPI:  más lento, más RAM, 3x menos código
         🟢 Node.js:   en medio en todo
         ☕ Java:       rápido pero pesadísimo
         ♦️ Rails:      lento pero te da todo hecho
```

FastAPI no es el más rápido, pero para una página que recibe ~500 req/s está sobrado. Y el código es **3-5x más corto** que en Go o Java.

Cuando te digan "es que en Go es más rápido", diles: "sí, pero el mío ya está en producción y lo escribí en una tarde" 🤷‍♂️

---

## Cómo correr los benchmarks tú mismo

```bash
git clone https://github.com/tu-usuario/letuchwebsite
cd letuchwebsite
uv sync
uv run pytest tests/benchmarks/
```

Solo necesitas `uv` instalado.

---

Hecho con ❤️ y muchas donas 🍩

*Fuentes: TechEmpower Round 22, CodeArchaeology 2026, Travis Luong benchmarks, AcquaintSoft 2026*
