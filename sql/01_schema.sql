-- ============================================================
-- ProyectoX — Subastas WoW
-- 01_schema.sql: DDL del modelo lógico 2.1 (PostgreSQL 15)
-- ============================================================

CREATE TABLE IF NOT EXISTS jugador (
    id_jugador      SERIAL PRIMARY KEY,
    nombre          VARCHAR(64)  NOT NULL,
    email           VARCHAR(128) UNIQUE NOT NULL,
    fecha_registro  TIMESTAMP    NOT NULL DEFAULT now(),
    wow_account_id  INTEGER UNIQUE
);

CREATE TABLE IF NOT EXISTS personaje (
    id_personaje SERIAL PRIMARY KEY,
    id_jugador   INTEGER NOT NULL REFERENCES jugador(id_jugador) ON DELETE CASCADE,
    nombre       VARCHAR(64) UNIQUE NOT NULL,
    nivel        INTEGER NOT NULL DEFAULT 1,
    clase        VARCHAR(30),
    oro          NUMERIC(12,2) NOT NULL DEFAULT 0,
    wow_guid     INTEGER UNIQUE,
    CONSTRAINT ck_personaje_nivel_oro CHECK (nivel >= 1 AND oro >= 0)
);

CREATE TABLE IF NOT EXISTS item (
    id_item         SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    rareza          VARCHAR(30) DEFAULT 'comun',
    nivel_requerido INTEGER DEFAULT 1,
    precio_base     NUMERIC(10,2) DEFAULT 0,
    wow_entry       INTEGER UNIQUE
);

CREATE TABLE IF NOT EXISTS inventario (
    id_inventario SERIAL PRIMARY KEY,
    id_personaje  INTEGER NOT NULL REFERENCES personaje(id_personaje) ON DELETE CASCADE,
    id_item       INTEGER NOT NULL REFERENCES item(id_item) ON DELETE CASCADE,
    cantidad      INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_inventario_personaje_item UNIQUE (id_personaje, id_item),
    CONSTRAINT ck_inventario_cantidad CHECK (cantidad > 0)
);

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

CREATE TABLE IF NOT EXISTS deposito (
    id_deposito SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    monto       NUMERIC(10,2) NOT NULL,
    pagado      BOOLEAN NOT NULL DEFAULT false,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS comision (
    id_comision SERIAL PRIMARY KEY,
    id_subasta  INTEGER NOT NULL UNIQUE REFERENCES subasta(id_subasta) ON DELETE CASCADE,
    porcentaje  NUMERIC(5,2) NOT NULL,
    monto       NUMERIC(10,2) NOT NULL,
    fecha       TIMESTAMP NOT NULL DEFAULT now()
);

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

-- Índices de apoyo
CREATE INDEX IF NOT EXISTS idx_personaje_jugador ON personaje(id_jugador);
CREATE INDEX IF NOT EXISTS idx_inventario_personaje ON inventario(id_personaje);
CREATE INDEX IF NOT EXISTS idx_subasta_estado ON subasta(estado);
CREATE INDEX IF NOT EXISTS idx_subasta_fin ON subasta(fecha_fin);
CREATE INDEX IF NOT EXISTS idx_puja_subasta ON puja(id_subasta);
CREATE INDEX IF NOT EXISTS idx_puja_comprador ON puja(id_comprador);
CREATE INDEX IF NOT EXISTS idx_correo_destinatario ON correo(id_destinatario);
