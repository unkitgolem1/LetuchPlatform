-- ============================================================
-- PostgreSQL Schema — LetuchWebSite v0.1.0
-- ============================================================
-- CREATE DATABASE letuchwebsite;
-- psql -U postgres -d letuchwebsite -f sql/001_schema.sql
-- ============================================================

-- 1. ENUMS ----------------------------------------------------

CREATE TYPE estado_carrito AS ENUM ('activo', 'convertido');

CREATE TYPE estado_pedido AS ENUM (
    'pendiente', 'confirmado', 'preparacion',
    'listo', 'entregado', 'cancelado'
);

CREATE TYPE tipo_contacto AS ENUM (
    'email', 'telefono', 'direccion',
    'instagram', 'facebook', 'horario'
);

-- 2. TABLAS ---------------------------------------------------

CREATE TABLE usuarios (
    id_usuario      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          VARCHAR(120) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    avatar          TEXT,
    miembros_desde  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE productos (
    id_producto     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo          VARCHAR(200) NOT NULL,
    descripcion     TEXT NOT NULL DEFAULT '',
    imagen          TEXT,
    precio          NUMERIC(10,2) NOT NULL DEFAULT 0,
    cantidad_stock  INTEGER NOT NULL DEFAULT 0,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE servicios (
    id_servicio     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo          VARCHAR(200) NOT NULL,
    descripcion     TEXT NOT NULL DEFAULT '',
    imagen          TEXT,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    orden           INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE carritos (
    id_carrito      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_usuario      UUID NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    estado          estado_carrito NOT NULL DEFAULT 'activo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE items_carrito (
    id_item         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_carrito      UUID NOT NULL REFERENCES carritos(id_carrito) ON DELETE CASCADE,
    id_producto     UUID NOT NULL REFERENCES productos(id_producto) ON DELETE CASCADE,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pedidos (
    id_pedido       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_usuario      UUID NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    fecha_pedido    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado          estado_pedido NOT NULL DEFAULT 'pendiente',
    total           NUMERIC(12,2) NOT NULL DEFAULT 0,
    notas           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE detalle_pedidos (
    id_detalle      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_pedido       UUID NOT NULL REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
    id_producto     UUID NOT NULL REFERENCES productos(id_producto) ON DELETE CASCADE,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL,
    subtotal        NUMERIC(12,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED
);

CREATE TABLE contactos_redes (
    id_contacto     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo            tipo_contacto NOT NULL,
    valor           TEXT NOT NULL,
    etiqueta        VARCHAR(100),
    orden           INTEGER NOT NULL DEFAULT 0,
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);

-- 3. INDEXES --------------------------------------------------

CREATE INDEX idx_carritos_usuario       ON carritos(id_usuario);
CREATE INDEX idx_items_carrito_carrito  ON items_carrito(id_carrito);
CREATE INDEX idx_items_carrito_producto ON items_carrito(id_producto);
CREATE INDEX idx_pedidos_usuario        ON pedidos(id_usuario);
CREATE INDEX idx_detalle_pedidos_pedido ON detalle_pedidos(id_pedido);
CREATE INDEX idx_productos_activo       ON productos(activo);
CREATE INDEX idx_servicios_activo_orden ON servicios(activo, orden);

-- 4. SEED DATA ------------------------------------------------

INSERT INTO usuarios (nombre, email, password_hash, avatar) VALUES
    ('Juan Pérez', 'juan@letuch.com', '$2b$12$placeholder_hash', NULL);

INSERT INTO servicios (titulo, descripcion, imagen, orden) VALUES
    ('Servicio de Vitrina',
     'Una muestra de nuestro pan fresco disponible en nuestras tiendas',
     '/static/images/caption.webp', 1),
    ('Servicio de Surtido a cafeterias',
     'Surtimos pan frezco y artesanal apartir de las 8:00AM',
     '/static/images/721266118_18538905730073817_2825081271361550579_n.jpg', 2),
    ('Larder & Kitchen',
     'Nacimos para el café, pero nuestra cocina de firma te hará volver.',
     '/static/images/borbon.jpg', 3),
    ('Culto al Café & Bebidas de Especialidad',
     'una carta de bebidas frías y calientes diseñada para complementar nuestra cocina',
     '/static/images/Bebida.jpg', 4);

INSERT INTO productos (titulo, descripcion, imagen, precio, cantidad_stock) VALUES
    ('Chocolatina', 'Delicioso pan de chocolate artesanal.', '', 52, 5);

INSERT INTO contactos_redes (tipo, valor, etiqueta, orden) VALUES
    ('instagram', 'https://www.instagram.com/letuchbakery/?hl=en', 'Instagram', 1),
    ('facebook',  'https://www.facebook.com/Letuchbakery/',        'Facebook',  2),
    ('direccion', '53D #195 x 40 y 42, Francisco de Montejo, 97203 Mérida, Yuc., Mexico', 'Dirección', 3),
    ('telefono',  '+52 999 171 8947', 'Teléfono', 4),
    ('email',     'letuchbakery@gmail.com', 'Correo electrónico', 5),
    ('horario',   'Lun–Sáb 8:00–20:00', 'Horario de atención', 6);
