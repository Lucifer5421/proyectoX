-- ============================================================
-- ProyectoX — Módulo de Subastas WoW
-- Esquema físico (DDL) + datos iniciales (DML)
-- Motor: PostgreSQL 15
-- ============================================================

-- ------------------------------------------------------------
-- 1. JUGADOR
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jugador (
    id_jugador SERIAL PRIMARY KEY,
    nombre     VARCHAR(64)  NOT NULL,
    email      VARCHAR(128) UNIQUE NOT NULL,
    oro        NUMERIC(12,2) NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 2. PERSONAJE
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS personaje (
    id_personaje SERIAL PRIMARY KEY,
    id_jugador   INTEGER NOT NULL REFERENCES jugador(id_jugador) ON DELETE CASCADE,
    nombre       VARCHAR(64) NOT NULL,
    nivel        INTEGER NOT NULL DEFAULT 1,
    clase        VARCHAR(30),
    oro          NUMERIC(12,2) NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 3. ITEM
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS item (
    id_item         SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    rareza          VARCHAR(30) DEFAULT 'comun',
    nivel_requerido INTEGER DEFAULT 1,
    precio_base     NUMERIC(10,2) DEFAULT 0
);

-- ------------------------------------------------------------
-- 4. INVENTARIO
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventario (
    id_inventario SERIAL PRIMARY KEY,
    id_personaje  INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item       INTEGER NOT NULL REFERENCES item(id_item) ON DELETE CASCADE,
    cantidad      INTEGER NOT NULL DEFAULT 1
);

-- ------------------------------------------------------------
-- 5. SUBASTA
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subasta (
    id_subasta            SERIAL PRIMARY KEY,
    id_vendedor           INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item               INTEGER NOT NULL REFERENCES item(id_item) ON DELETE CASCADE,
    cantidad              INTEGER NOT NULL DEFAULT 1,
    precio_salida         NUMERIC(10,2) NOT NULL,
    precio_compra_directa NUMERIC(10,2),
    duracion_horas        INTEGER NOT NULL DEFAULT 24 CHECK (duracion_horas IN (2, 8, 24)),
    estado                VARCHAR(20) NOT NULL DEFAULT 'activa',
    fecha_inicio          TIMESTAMP NOT NULL DEFAULT now(),
    fecha_fin             TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------
-- 6. PUJA
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS puja (
    id_puja      SERIAL PRIMARY KEY,
    id_subasta   INTEGER NOT NULL REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    id_comprador INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    monto        NUMERIC(10,2) NOT NULL,
    estado       VARCHAR(20) NOT NULL DEFAULT 'activa',
    fecha        TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 7. DEPOSITO
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deposito (
    id_deposito SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    monto       NUMERIC(10,2) NOT NULL,
    pagado      BOOLEAN NOT NULL DEFAULT false,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 8. COMISION
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comision (
    id_comision SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    porcentaje  NUMERIC(5,2) NOT NULL,
    monto       NUMERIC(10,2) NOT NULL,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 9. TRANSACCION
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaccion (
    id_transaccion SERIAL PRIMARY KEY,
    id_subasta     INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    id_comprador   INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_vendedor    INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    monto          NUMERIC(10,2) NOT NULL,
    tipo           VARCHAR(20) NOT NULL,
    fecha          TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 10. CORREO
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS correo (
    id_correo       SERIAL PRIMARY KEY,
    id_destinatario INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item         INTEGER REFERENCES item(id_item) ON DELETE SET NULL,
    cantidad        INTEGER DEFAULT 0,
    oro             NUMERIC(12,2) DEFAULT 0,
    asunto          VARCHAR(150) NOT NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    fecha           TIMESTAMP NOT NULL DEFAULT now()
);

-- ============================================================
-- DATOS INICIALES (idempotentes)
-- ============================================================

INSERT INTO jugador (nombre, email, oro) VALUES
    ('Luis',    'luis@example.com',    10000.00),
    ('Aracely', 'aracely@example.com',  5000.00)
ON CONFLICT (email) DO NOTHING;

INSERT INTO personaje (id_jugador, nombre, nivel, clase, oro)
SELECT j.id_jugador, 'Luis', 80, 'Paladin', 10000.00
FROM jugador j
WHERE j.email = 'luis@example.com'
  AND NOT EXISTS (SELECT 1 FROM personaje p WHERE p.nombre = 'Luis');

INSERT INTO personaje (id_jugador, nombre, nivel, clase, oro)
SELECT j.id_jugador, 'Aracely', 1, 'Mage', 5000.00
FROM jugador j
WHERE j.email = 'aracely@example.com'
  AND NOT EXISTS (SELECT 1 FROM personaje p WHERE p.nombre = 'Aracely');

INSERT INTO item (nombre, rareza, nivel_requerido, precio_base)
SELECT 'Espada de fuego', 'epica', 60, 500.00
WHERE NOT EXISTS (SELECT 1 FROM item WHERE nombre = 'Espada de fuego');

INSERT INTO item (nombre, rareza, nivel_requerido, precio_base)
SELECT 'Poción de maná', 'comun', 1, 5.00
WHERE NOT EXISTS (SELECT 1 FROM item WHERE nombre = 'Poción de maná');

INSERT INTO item (nombre, rareza, nivel_requerido, precio_base)
SELECT 'Tela de lino', 'comun', 1, 2.00
WHERE NOT EXISTS (SELECT 1 FROM item WHERE nombre = 'Tela de lino');

INSERT INTO inventario (id_personaje, id_item, cantidad)
SELECT p.id_personaje, i.id_item, 1
FROM personaje p, item i
WHERE p.nombre = 'Luis'
  AND i.nombre = 'Espada de fuego'
  AND NOT EXISTS (
      SELECT 1 FROM inventario inv
      WHERE inv.id_personaje = p.id_personaje AND inv.id_item = i.id_item
  );

INSERT INTO inventario (id_personaje, id_item, cantidad)
SELECT p.id_personaje, i.id_item, 10
FROM personaje p, item i
WHERE p.nombre = 'Aracely'
  AND i.nombre = 'Poción de maná'
  AND NOT EXISTS (
      SELECT 1 FROM inventario inv
      WHERE inv.id_personaje = p.id_personaje AND inv.id_item = i.id_item
  );

-- Material extra para el ejemplo de publicación de la API.
INSERT INTO inventario (id_personaje, id_item, cantidad)
SELECT p.id_personaje, i.id_item, 5
FROM personaje p, item i
WHERE p.nombre = 'Luis'
  AND i.nombre = 'Tela de lino'
  AND NOT EXISTS (
      SELECT 1 FROM inventario inv
      WHERE inv.id_personaje = p.id_personaje AND inv.id_item = i.id_item
  );

-- Subasta de ejemplo (opcional).
-- La CTE solo descuenta el ítem si la subasta se insertó de verdad,
-- así el seed es idempotente.
WITH nueva AS (
    INSERT INTO subasta (
        id_vendedor, id_item, cantidad, precio_salida,
        precio_compra_directa, duracion_horas, estado, fecha_fin
    )
    SELECT p.id_personaje, i.id_item, 1, 100.00, 250.00, 24, 'activa',
           now() + interval '24 hours'
    FROM personaje p, item i
    WHERE p.nombre = 'Luis'
      AND i.nombre = 'Espada de fuego'
      AND NOT EXISTS (
          SELECT 1 FROM subasta s
          WHERE s.id_vendedor = p.id_personaje
            AND s.id_item = i.id_item
            AND s.estado = 'activa'
      )
    RETURNING id_vendedor, id_item
)
UPDATE inventario inv
SET cantidad = inv.cantidad - 1
FROM nueva n
WHERE inv.id_personaje = n.id_vendedor
  AND inv.id_item = n.id_item
  AND inv.cantidad > 0;

DELETE FROM inventario WHERE cantidad <= 0;

-- Depósito de la subasta de ejemplo (5% de 100 = 5).
-- La CTE solo descuenta el oro si el depósito se insertó de verdad.
WITH dep AS (
    INSERT INTO deposito (id_subasta, monto, pagado)
    SELECT s.id_subasta, 5.00, true
    FROM subasta s
    WHERE s.id_vendedor = (SELECT id_personaje FROM personaje WHERE nombre = 'Luis')
      AND s.id_item = (SELECT id_item FROM item WHERE nombre = 'Espada de fuego')
      AND s.estado = 'activa'
      AND NOT EXISTS (
          SELECT 1 FROM deposito d WHERE d.id_subasta = s.id_subasta
      )
    RETURNING id_subasta
)
UPDATE personaje p
SET oro = p.oro - 5.00
FROM subasta s
JOIN dep ON dep.id_subasta = s.id_subasta
WHERE p.id_personaje = s.id_vendedor;
