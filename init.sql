-- ============================================================
-- ProyectoX — Subastas WoW
-- Esquema físico (DDL) del modelo lógico 2.1
-- Motor: PostgreSQL 15
-- Fuente: modelo_subastas(2.1).drawio
--
-- Este archivo contiene SOLO DDL: base de datos, tablas, tipos,
-- claves primarias, claves foráneas, restricciones e índices.
-- Los datos de demostración viven en sql/02_seed.sql.
-- ============================================================

-- ============================================================
-- MÓDULO auth — Cuentas y personajes
-- Relación: JUGADOR (1) ──< (N) PERSONAJE
-- ============================================================

-- ------------------------------------------------------------
-- auth · JUGADOR
-- PK: id_jugador
-- UK: email
-- Cardinalidad: 1 jugador tiene N personajes.
-- Regla: el oro NO vive en el jugador; vive en el personaje.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jugador (
    id_jugador      SERIAL PRIMARY KEY,
    nombre          VARCHAR(64)  NOT NULL,
    email           VARCHAR(128) UNIQUE NOT NULL,
    fecha_registro  TIMESTAMP    NOT NULL DEFAULT now(),
    -- Columna técnica de integración con AzerothCore.
    -- No pertenece al modelo lógico 2.1.
    wow_account_id  INTEGER UNIQUE
);

-- ------------------------------------------------------------
-- auth · PERSONAJE
-- PK: id_personaje
-- FK: id_jugador -> jugador.id_jugador (ON DELETE CASCADE)
-- UK: nombre
-- Cardinalidad:
--   N personajes pertenecen a 1 jugador.
--   1 personaje publica N subastas (subasta.id_vendedor).
--   1 personaje realiza N pujas (puja.id_comprador).
--   1 personaje compra N transacciones (transaccion.id_comprador).
--   1 personaje recibe N correos (correo.id_destinatario).
--   N personajes poseen M ítems mediante inventario.
-- Reglas: nivel >= 1 y oro >= 0.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS personaje (
    id_personaje SERIAL PRIMARY KEY,
    id_jugador   INTEGER NOT NULL REFERENCES jugador(id_jugador) ON DELETE CASCADE,
    nombre       VARCHAR(64) UNIQUE NOT NULL,
    nivel        INTEGER NOT NULL DEFAULT 1,
    clase        VARCHAR(30),
    oro          NUMERIC(12,2) NOT NULL DEFAULT 0,
    -- GUID del personaje en acore_characters.characters.
    -- No pertenece al modelo lógico 2.1.
    wow_guid     INTEGER UNIQUE,
    CONSTRAINT ck_personaje_nivel_oro CHECK (nivel >= 1 AND oro >= 0)
);

-- ============================================================
-- MÓDULO inventory — Catálogo de ítems e inventario
-- Relación: PERSONAJE (N) ──< INVENTARIO >── (M) ITEM
-- ============================================================

-- ------------------------------------------------------------
-- inventory · ITEM
-- PK: id_item
-- Cardinalidad:
--   1 ítem puede estar en N inventarios.
--   1 ítem puede publicarse en N subastas (subasta.id_item).
--   1 ítem puede adjuntarse a N correos (correo.id_item).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS item (
    id_item         SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    rareza          VARCHAR(30) DEFAULT 'comun',
    nivel_requerido INTEGER DEFAULT 1,
    precio_base     NUMERIC(10,2) DEFAULT 0,
    -- entry de acore_world.item_template.
    -- No pertenece al modelo lógico 2.1.
    wow_entry       INTEGER UNIQUE
);

-- ------------------------------------------------------------
-- inventory · INVENTARIO
-- PK: id_inventario
-- FK: id_personaje -> personaje.id_personaje (ON DELETE CASCADE)
-- FK: id_item      -> item.id_item           (ON DELETE CASCADE)
-- UK: (id_personaje, id_item)
-- Cardinalidad: resuelve la relación N:M entre personaje e ítem.
-- Regla: cantidad > 0.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventario (
    id_inventario SERIAL PRIMARY KEY,
    id_personaje  INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item       INTEGER NOT NULL REFERENCES item(id_item) ON DELETE CASCADE,
    cantidad      INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_inventario_personaje_item UNIQUE (id_personaje, id_item),
    CONSTRAINT ck_inventario_cantidad CHECK (cantidad > 0)
);

-- ============================================================
-- MÓDULO auction — Subastas y pujas
-- Relación: SUBASTA (1) ──< (N) PUJA
-- ============================================================

-- ------------------------------------------------------------
-- auction · SUBASTA
-- PK: id_subasta
-- FK: id_vendedor -> personaje.id_personaje (ON DELETE CASCADE)
-- FK: id_item     -> item.id_item           (ON DELETE CASCADE)
-- Cardinalidad:
--   N subastas pertenecen a 1 personaje vendedor.
--   N subastas ofrecen 1 ítem.
--   1 subasta recibe N pujas.
--   1 subasta origina 1 transacción, 1 depósito y 1 comisión.
-- Reglas:
--   duracion_horas IN (2, 8, 24)
--   estado IN (activa, vendida, expirada, cancelada)
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
-- auction · PUJA
-- PK: id_puja
-- FK: id_subasta   -> subasta.id_subasta    (ON DELETE CASCADE)
-- FK: id_comprador -> personaje.id_personaje (ON DELETE CASCADE)
-- Cardinalidad:
--   N pujas pertenecen a 1 subasta.
--   N pujas son realizadas por 1 personaje comprador.
-- Regla: estado IN (activa, superada, ganadora).
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

-- ============================================================
-- MÓDULO finance — Depósitos, comisiones y transacciones
-- Cada entidad se relaciona 1:1 con SUBASTA.
-- ============================================================

-- ------------------------------------------------------------
-- finance · DEPOSITO
-- PK: id_deposito
-- FK: id_subasta -> subasta.id_subasta (ON DELETE CASCADE)
-- UK: id_subasta (relación 1:1)
-- Regla: garantía pagada por el vendedor al publicar.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deposito (
    id_deposito SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    monto       NUMERIC(10,2) NOT NULL,
    pagado      BOOLEAN NOT NULL DEFAULT false,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- finance · COMISION
-- PK: id_comision
-- FK: id_subasta -> subasta.id_subasta (ON DELETE CASCADE)
-- UK: id_subasta (relación 1:1)
-- Regla: comisión que cobra la casa de subastas al cerrar la venta.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comision (
    id_comision SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    porcentaje  NUMERIC(5,2) NOT NULL,
    monto       NUMERIC(10,2) NOT NULL,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- finance · TRANSACCION
-- PK: id_transaccion
-- FK: id_subasta   -> subasta.id_subasta     (ON DELETE CASCADE)
-- FK: id_comprador -> personaje.id_personaje (ON DELETE CASCADE)
-- UK: id_subasta (relación 1:1 con la subasta)
-- Cardinalidad: N transacciones son realizadas por 1 personaje.
-- Regla: tipo IN (puja_ganadora, compra_directa).
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

-- ============================================================
-- MÓDULO mail — Correo del personaje
-- Relación: PERSONAJE (1) ──< (N) CORREO >── (0..1) ITEM
-- ============================================================

-- ------------------------------------------------------------
-- mail · CORREO
-- PK: id_correo
-- FK: id_destinatario -> personaje.id_personaje (ON DELETE CASCADE)
-- FK: id_item         -> item.id_item           (ON DELETE SET NULL)
-- Cardinalidad:
--   N correos pertenecen a 1 personaje destinatario.
--   N correos pueden adjuntar 1 ítem; id_item admite NULL.
-- Regla: estado IN (pendiente, leido, cobrado, devuelto).
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

-- ============================================================
-- Índices de apoyo (no forman parte de las relaciones del modelo)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_personaje_jugador ON personaje(id_jugador);
CREATE INDEX IF NOT EXISTS idx_inventario_personaje ON inventario(id_personaje);
CREATE INDEX IF NOT EXISTS idx_subasta_estado ON subasta(estado);
CREATE INDEX IF NOT EXISTS idx_subasta_fin ON subasta(fecha_fin);
CREATE INDEX IF NOT EXISTS idx_puja_subasta ON puja(id_subasta);
CREATE INDEX IF NOT EXISTS idx_puja_comprador ON puja(id_comprador);
CREATE INDEX IF NOT EXISTS idx_correo_destinatario ON correo(id_destinatario);
