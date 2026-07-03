-- =====================================================
-- Supabase Setup: Tabla, índices y vistas
-- Pega esto en el SQL Editor de Supabase
-- =====================================================

-- 1. TABLA
CREATE TABLE IF NOT EXISTS productos (
  id          BIGSERIAL PRIMARY KEY,
  nombre      TEXT NOT NULL,
  precio      NUMERIC(10,2) NOT NULL,
  descripcion TEXT,
  categoria   TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- 2. ÍNDICES
CREATE INDEX IF NOT EXISTS idx_productos_categoria  ON productos (categoria);
CREATE INDEX IF NOT EXISTS idx_productos_nombre     ON productos (nombre);
CREATE INDEX IF NOT EXISTS idx_productos_cat_nombre ON productos (categoria, nombre);

-- 3. VISTAS (consultas para el frontend)

-- Pan dulce
CREATE OR REPLACE VIEW vista_pan_dulce AS
SELECT id, nombre, precio, descripcion
FROM productos
WHERE categoria = 'PANADERIA DULCE'
ORDER BY nombre;

-- Pan salado
CREATE OR REPLACE VIEW vista_pan_salado AS
SELECT id, nombre, precio, descripcion
FROM productos
WHERE categoria = 'PANADERIA SALADA'
ORDER BY nombre;

-- Bebidas (calientes + frías)
CREATE OR REPLACE VIEW vista_bebidas AS
SELECT id, nombre, precio, descripcion, categoria
FROM productos
WHERE categoria IN ('BEBIDAS CALIENTES', 'BEBIDAS FRIAS')
ORDER BY categoria, nombre;

-- Platillos
CREATE OR REPLACE VIEW vista_platillos AS
SELECT id, nombre, precio, descripcion
FROM productos
WHERE categoria = 'DESAYUNO-CENA'
ORDER BY nombre;

-- Productos locales
CREATE OR REPLACE VIEW vista_productos_locales AS
SELECT id, nombre, precio, descripcion
FROM productos
WHERE categoria = 'PRODUCTOS LOCALES'
ORDER BY nombre;

-- Postres
CREATE OR REPLACE VIEW vista_postres AS
SELECT id, nombre, precio, descripcion
FROM productos
WHERE categoria = 'POSTRES'
ORDER BY nombre;

-- Pan de temporada
CREATE OR REPLACE VIEW vista_temporada AS
SELECT id, nombre, precio, descripcion
FROM productos
WHERE categoria = 'PAN DE TEMPORADA'
ORDER BY nombre;

-- 4. VISTA auxiliar: conteo para las etiquetas del frontend
CREATE OR REPLACE VIEW vista_categorias_conteo AS
SELECT categoria, COUNT(*) AS total
FROM productos
GROUP BY categoria
ORDER BY categoria;
