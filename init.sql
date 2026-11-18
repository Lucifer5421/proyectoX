-- ============================================================
-- ProyectoX — Módulo de Subastas WoW
-- Esquema físico (DDL) + datos iniciales (DML)
-- Motor: PostgreSQL 15
-- Basado en modelo_subastas(2.1).drawio
-- ============================================================

-- ------------------------------------------------------------
-- 1. JUGADOR (módulo auth)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jugador (
    id_jugador      SERIAL PRIMARY KEY,
    nombre          VARCHAR(64)  NOT NULL,
    email           VARCHAR(128) UNIQUE NOT NULL,
    fecha_registro  TIMESTAMP    NOT NULL DEFAULT now(),
    -- Columna técnica de integración con AzerothCore (no está en el
    -- modelo lógico del drawio).
    wow_account_id  INTEGER UNIQUE
);

-- ------------------------------------------------------------
-- 2. PERSONAJE (módulo auth)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS personaje (
    id_personaje SERIAL PRIMARY KEY,
    id_jugador   INTEGER NOT NULL REFERENCES jugador(id_jugador) ON DELETE CASCADE,
    nombre       VARCHAR(64) UNIQUE NOT NULL,
    nivel        INTEGER NOT NULL DEFAULT 1,
    clase        VARCHAR(30),
    oro          NUMERIC(12,2) NOT NULL DEFAULT 0,
    -- GUID del personaje en acore_characters.characters.
    wow_guid     INTEGER UNIQUE,
    CONSTRAINT ck_personaje_nivel_oro CHECK (nivel >= 1 AND oro >= 0)
);

-- ------------------------------------------------------------
-- 3. ITEM (módulo restaurant)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS item (
    id_item         SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    rareza          VARCHAR(30) DEFAULT 'comun',
    nivel_requerido INTEGER DEFAULT 1,
    precio_base     NUMERIC(10,2) DEFAULT 0,
    -- entry de acore_world.item_template.
    wow_entry       INTEGER UNIQUE
);

-- ------------------------------------------------------------
-- 4. INVENTARIO (módulo restaurant)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventario (
    id_inventario SERIAL PRIMARY KEY,
    id_personaje  INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item       INTEGER NOT NULL REFERENCES item(id_item) ON DELETE CASCADE,
    cantidad      INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_inventario_personaje_item UNIQUE (id_personaje, id_item),
    CONSTRAINT ck_inventario_cantidad CHECK (cantidad > 0)
);

-- ------------------------------------------------------------
-- 5. SUBASTA (módulo order)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subasta (
    id_subasta            SERIAL PRIMARY KEY,
    id_vendedor           INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item               INTEGER NOT NULL REFERENCES item(id_item) ON DELETE CASCADE,
    cantidad              INTEGER NOT NULL DEFAULT 1,
    precio_salida         NUMERIC(10,2) NOT NULL,
    precio_compra_directa NUMERIC(10,2),
    duracion_horas        INTEGER NOT NULL DEFAULT 24,
    estado                VARCHAR(20) NOT NULL DEFAULT 'activa',
    fecha_inicio          TIMESTAMP NOT NULL DEFAULT now(),
    fecha_fin             TIMESTAMP NOT NULL,
    CONSTRAINT ck_duracion_subasta CHECK (duracion_horas IN (2, 8, 24)),
    CONSTRAINT ck_estado_subasta CHECK (
        estado IN ('activa', 'vendida', 'expirada', 'cancelada')
    )
);

-- ------------------------------------------------------------
-- 6. PUJA (módulo order)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS puja (
    id_puja      SERIAL PRIMARY KEY,
    id_subasta   INTEGER NOT NULL REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    id_comprador INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    monto        NUMERIC(10,2) NOT NULL,
    estado       VARCHAR(20) NOT NULL DEFAULT 'activa',
    fecha        TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT ck_estado_puja CHECK (
        estado IN ('activa', 'superada', 'ganadora')
    )
);

-- ------------------------------------------------------------
-- 7. DEPOSITO (módulo payment)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deposito (
    id_deposito SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    monto       NUMERIC(10,2) NOT NULL,
    pagado      BOOLEAN NOT NULL DEFAULT false,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 8. COMISION (módulo payment)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comision (
    id_comision SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    porcentaje  NUMERIC(5,2) NOT NULL,
    monto       NUMERIC(10,2) NOT NULL,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- 9. TRANSACCION (módulo payment)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaccion (
    id_transaccion SERIAL PRIMARY KEY,
    id_subasta     INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    id_comprador   INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    monto          NUMERIC(10,2) NOT NULL,
    tipo           VARCHAR(20) NOT NULL,
    fecha          TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT ck_tipo_transaccion CHECK (
        tipo IN ('puja_ganadora', 'compra_directa')
    )
);

-- ------------------------------------------------------------
-- 10. CORREO (módulo payment)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS correo (
    id_correo       SERIAL PRIMARY KEY,
    id_destinatario INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item         INTEGER REFERENCES item(id_item) ON DELETE SET NULL,
    cantidad        INTEGER DEFAULT 0,
    oro             NUMERIC(12,2) DEFAULT 0,
    asunto          VARCHAR(150) NOT NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    fecha           TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT ck_estado_correo CHECK (
        estado IN ('pendiente', 'leido', 'cobrado', 'devuelto')
    )
);

-- ------------------------------------------------------------
-- Índices de apoyo
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_personaje_jugador ON personaje(id_jugador);
CREATE INDEX IF NOT EXISTS idx_inventario_personaje ON inventario(id_personaje);
CREATE INDEX IF NOT EXISTS idx_subasta_estado ON subasta(estado);
CREATE INDEX IF NOT EXISTS idx_subasta_fin ON subasta(fecha_fin);
CREATE INDEX IF NOT EXISTS idx_puja_subasta ON puja(id_subasta);
CREATE INDEX IF NOT EXISTS idx_puja_comprador ON puja(id_comprador);
CREATE INDEX IF NOT EXISTS idx_correo_destinatario ON correo(id_destinatario);

-- ============================================================
-- DATOS INICIALES (idempotentes)
-- ============================================================

INSERT INTO jugador (nombre, email) VALUES
    ('Luis',    'luis@example.com'),
    ('Aracely', 'aracely@example.com')
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
SELECT p.id_personaje, i.id_item, 2
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
