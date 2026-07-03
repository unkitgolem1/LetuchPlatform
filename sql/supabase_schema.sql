-- ============================================================
-- Supabase Schema — Sesiones, Usuarios, Carrito + índices
-- Pega esto en el SQL Editor de Supabase (una sola vez)
-- ============================================================

-- 1. EXTENSIONES (si no existen)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 2. MIGRACIÓN: columnas faltantes en productos (supabase_setup.sql)
-- ============================================================
ALTER TABLE productos ADD COLUMN IF NOT EXISTS imagen       TEXT;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS cantidad_stock INTEGER NOT NULL DEFAULT 0;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS activo         BOOLEAN NOT NULL DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo) WHERE activo = TRUE;

-- ============================================================
-- 3. TABLAS NUEVAS
-- ============================================================

-- 2.1 Sesiones (guest before login)
CREATE TABLE IF NOT EXISTS sesiones (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days')
);

-- 2.2 Usuarios (cuando el guest decide registrarse)
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_sesion       UUID UNIQUE REFERENCES sesiones(id) ON DELETE CASCADE,
    nombre          VARCHAR(120),
    email           VARCHAR(255) UNIQUE,
    password_hash   VARCHAR(255),
    avatar          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.3 Carritos (uno por sesión activa)
CREATE TABLE IF NOT EXISTS carritos (
    id_carrito      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_sesion       UUID NOT NULL REFERENCES sesiones(id) ON DELETE CASCADE,
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo'
                    CHECK (estado IN ('activo', 'convertido', 'abandonado')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.4 Items del carrito
CREATE TABLE IF NOT EXISTS items_carrito (
    id_item         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_carrito      UUID NOT NULL REFERENCES carritos(id_carrito) ON DELETE CASCADE,
    id_producto     BIGINT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 4. ÍNDICES
-- ============================================================

-- Sesiones: búsqueda por cookie
CREATE INDEX IF NOT EXISTS idx_sesiones_id ON sesiones(id);

-- Usuarios: búsqueda por sesión y por email
CREATE INDEX IF NOT EXISTS idx_usuarios_sesion   ON usuarios(id_sesion);
CREATE INDEX IF NOT EXISTS idx_usuarios_email    ON usuarios(email) WHERE email IS NOT NULL;

-- Carritos: sesión activa (el más usado)
CREATE INDEX IF NOT EXISTS idx_carritos_sesion_activo
    ON carritos(id_sesion, estado)
    WHERE estado = 'activo';

-- Items: carrito padre (JOIN rápido)
CREATE INDEX IF NOT EXISTS idx_items_carrito_carrito  ON items_carrito(id_carrito);
CREATE INDEX IF NOT EXISTS idx_items_carrito_producto ON items_carrito(id_producto);

-- Unicidad: un mismo producto aparece una sola vez por carrito (para upsert)
CREATE UNIQUE INDEX IF NOT EXISTS idx_items_carrito_unico
    ON items_carrito(id_carrito, id_producto);

-- ============================================================
-- 5. VISTAS (para los repos de Python)
-- ============================================================

-- 4.1 Carrito completo con datos del producto
CREATE OR REPLACE VIEW vista_carrito_detalle AS
SELECT
    c.id_carrito,
    c.id_sesion,
    c.estado,
    ic.id_item,
    ic.id_producto,
    p.nombre          AS titulo,
    p.descripcion,
    p.precio          AS precio_actual,
    ic.precio_unitario,
    ic.cantidad,
    (ic.precio_unitario * ic.cantidad)::NUMERIC(12,2) AS subtotal
FROM carritos c
JOIN items_carrito ic ON ic.id_carrito = c.id_carrito
JOIN productos p      ON p.id          = ic.id_producto
WHERE c.estado = 'activo'
ORDER BY ic.created_at;

-- 4.2 Totales del carrito por sesión
CREATE OR REPLACE VIEW vista_carrito_totales AS
SELECT
    c.id_sesion,
    c.id_carrito,
    COUNT(ic.id_item)                        AS cantidad_items,
    SUM(ic.cantidad)                         AS cantidad_productos,
    SUM(ic.precio_unitario * ic.cantidad)::NUMERIC(12,2) AS total
FROM carritos c
LEFT JOIN items_carrito ic ON ic.id_carrito = c.id_carrito
WHERE c.estado = 'activo'
GROUP BY c.id_sesion, c.id_carrito;

-- 4.3 Sesiones expiradas (para limpieza periódica)
CREATE OR REPLACE VIEW vista_sesiones_expiradas AS
SELECT id, created_at, expires_at
FROM sesiones
WHERE expires_at < NOW();

-- ============================================================
-- 6. FUNCIÓN: obtener o crear sesión (para el backend)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_obtener_o_crear_sesion(p_id_sesion UUID DEFAULT NULL)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID;
BEGIN
    -- Si ya existe y no ha expirado, la regresa
    IF p_id_sesion IS NOT NULL THEN
        SELECT id INTO v_id FROM sesiones
        WHERE id = p_id_sesion AND expires_at > NOW();
        IF FOUND THEN
            -- Extiende expiración
            UPDATE sesiones SET expires_at = NOW() + INTERVAL '30 days'
            WHERE id = v_id;
            RETURN v_id;
        END IF;
    END IF;

    -- Si no existe o expiró, crea una nueva
    INSERT INTO sesiones (id) VALUES (gen_random_uuid()) RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;

-- ============================================================
-- 7. FUNCIÓN: asegurar carrito activo para una sesión
-- ============================================================
CREATE OR REPLACE FUNCTION fn_obtener_o_crear_carrito(p_id_sesion UUID)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID;
BEGIN
    SELECT id_carrito INTO v_id FROM carritos
    WHERE id_sesion = p_id_sesion AND estado = 'activo'
    LIMIT 1;

    IF NOT FOUND THEN
        INSERT INTO carritos (id_sesion, estado)
        VALUES (p_id_sesion, 'activo')
        RETURNING id_carrito INTO v_id;
    END IF;

    RETURN v_id;
END;
$$;

-- ============================================================
-- 8. PEDIDOS (órdenes de compra)
-- ============================================================
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_sesion       UUID NOT NULL REFERENCES sesiones(id) ON DELETE CASCADE,
    id_usuario      UUID REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente', 'confirmado', 'entregado', 'cancelado')),
    total           NUMERIC(12,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id_pedido_item  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_pedido       UUID NOT NULL REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
    id_producto     BIGINT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    titulo          VARCHAR(255) NOT NULL,
    imagen          TEXT NOT NULL DEFAULT '',
    precio_unitario NUMERIC(10,2) NOT NULL,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    subtotal        NUMERIC(12,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pedidos_sesion   ON pedidos(id_sesion);
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario  ON pedidos(id_usuario) WHERE id_usuario IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pedido_items_pedido ON pedido_items(id_pedido);

CREATE OR REPLACE VIEW vista_pedidos AS
SELECT
    p.id_pedido,
    p.id_sesion,
    p.id_usuario,
    p.estado,
    p.total,
    p.created_at,
    COUNT(pi.id_pedido_item)::INTEGER AS cantidad_items,
    COALESCE(SUM(pi.cantidad), 0)::INTEGER AS cantidad_productos
FROM pedidos p
LEFT JOIN pedido_items pi ON pi.id_pedido = p.id_pedido
GROUP BY p.id_pedido, p.id_sesion, p.id_usuario, p.estado, p.total, p.created_at
ORDER BY p.created_at DESC;

-- ============================================================
-- 9. VISTA: productos para la vitrina (con categoría y stock)
-- ============================================================
CREATE OR REPLACE VIEW vista_productos_vitrina AS
SELECT
    id,
    nombre           AS titulo,
    descripcion,
    COALESCE(imagen, '') AS imagen,
    precio,
    cantidad_stock   AS cantidad,
    categoria,
    activo
FROM productos
WHERE activo = TRUE
ORDER BY categoria, nombre;
