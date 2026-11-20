-- ============================================================
-- ProyectoX — 03_integracion_wow.sql
-- Ajusta una base existente al modelo lógico 2.1 y agrega las
-- claves externas de AzerothCore para la sincronización de solo lectura.
--
-- Ejecutar una vez sobre una base ya existente:
--   docker exec -i proyectoX-db sh -c \
--     'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
--     < sql/03_integracion_wow.sql
--
-- En una instalación nueva, init.sql / 01_schema.sql ya incluyen
-- estas columnas y restricciones.
-- ============================================================

-- ------------------------------------------------------------
-- 1. MÓDULO auth · JUGADOR: el oro pertenece al personaje, no a la cuenta.
-- ------------------------------------------------------------
ALTER TABLE jugador ADD COLUMN IF NOT EXISTS fecha_registro TIMESTAMP;
UPDATE jugador SET fecha_registro = now() WHERE fecha_registro IS NULL;
ALTER TABLE jugador ALTER COLUMN fecha_registro SET DEFAULT now();
ALTER TABLE jugador ALTER COLUMN fecha_registro SET NOT NULL;
ALTER TABLE jugador DROP COLUMN IF EXISTS oro;

-- ------------------------------------------------------------
-- 2. MÓDULO auth · PERSONAJE: nombre único y checks del modelo.
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_personaje_nombre'
          AND conrelid = 'personaje'::regclass
    ) THEN
        ALTER TABLE personaje
            ADD CONSTRAINT uq_personaje_nombre UNIQUE (nombre);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_personaje_nivel_oro'
          AND conrelid = 'personaje'::regclass
    ) THEN
        ALTER TABLE personaje
            ADD CONSTRAINT ck_personaje_nivel_oro
            CHECK (nivel >= 1 AND oro >= 0);
    END IF;
END $$;

-- ------------------------------------------------------------
-- 3. MÓDULO inventory · ITEM: el modelo 2.1 limita el nombre a 100 caracteres.
-- ------------------------------------------------------------
UPDATE item SET nombre = LEFT(nombre, 100) WHERE length(nombre) > 100;
ALTER TABLE item ALTER COLUMN nombre TYPE VARCHAR(100);

-- ------------------------------------------------------------
-- 4. MÓDULO inventory · INVENTARIO: cantidad positiva.
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_inventario_cantidad'
          AND conrelid = 'inventario'::regclass
    ) THEN
        ALTER TABLE inventario
            ADD CONSTRAINT ck_inventario_cantidad CHECK (cantidad > 0);
    END IF;
END $$;

-- ------------------------------------------------------------
-- 5. MÓDULO auction · SUBASTA: duración y estados permitidos.
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_duracion_subasta'
          AND conrelid = 'subasta'::regclass
    ) THEN
        ALTER TABLE subasta
            ADD CONSTRAINT ck_duracion_subasta
            CHECK (duracion_horas IN (2, 8, 24));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_estado_subasta'
          AND conrelid = 'subasta'::regclass
    ) THEN
        ALTER TABLE subasta
            ADD CONSTRAINT ck_estado_subasta
            CHECK (estado IN ('activa', 'vendida', 'expirada', 'cancelada'));
    END IF;
END $$;

-- ------------------------------------------------------------
-- 6. MÓDULO auction · PUJA: estados permitidos.
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_estado_puja'
          AND conrelid = 'puja'::regclass
    ) THEN
        ALTER TABLE puja
            ADD CONSTRAINT ck_estado_puja
            CHECK (estado IN ('activa', 'superada', 'ganadora'));
    END IF;
END $$;

-- ------------------------------------------------------------
-- 7. MÓDULO finance · TRANSACCION: el vendedor se deduce de subasta; tipo del modelo.
-- ------------------------------------------------------------
ALTER TABLE transaccion DROP COLUMN IF EXISTS id_vendedor;
UPDATE transaccion SET tipo = 'puja_ganadora' WHERE tipo = 'puja';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_tipo_transaccion'
          AND conrelid = 'transaccion'::regclass
    ) THEN
        ALTER TABLE transaccion
            ADD CONSTRAINT ck_tipo_transaccion
            CHECK (tipo IN ('puja_ganadora', 'compra_directa'));
    END IF;
END $$;

-- ------------------------------------------------------------
-- 8. MÓDULO mail · CORREO: estados del modelo 2.1.
-- ------------------------------------------------------------
UPDATE correo SET estado = 'cobrado' WHERE estado = 'entregado';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_estado_correo'
          AND conrelid = 'correo'::regclass
    ) THEN
        ALTER TABLE correo
            ADD CONSTRAINT ck_estado_correo
            CHECK (estado IN ('pendiente', 'leido', 'cobrado', 'devuelto'));
    END IF;
END $$;

-- ------------------------------------------------------------
-- 9. Integración WoW · columnas técnicas en auth e inventory.
-- QUÉ HACE: claves externas de AzerothCore (fuera del modelo lógico 2.1).
-- ------------------------------------------------------------
ALTER TABLE jugador   ADD COLUMN IF NOT EXISTS wow_account_id INTEGER;
ALTER TABLE personaje ADD COLUMN IF NOT EXISTS wow_guid INTEGER;
ALTER TABLE item      ADD COLUMN IF NOT EXISTS wow_entry INTEGER;

-- Consolidar posibles duplicados antes de crear el índice único.
WITH duplicados AS (
    SELECT id_personaje,
           id_item,
           SUM(cantidad) AS total,
           MIN(id_inventario) AS conservar
    FROM inventario
    GROUP BY id_personaje, id_item
    HAVING COUNT(*) > 1
)
UPDATE inventario i
SET cantidad = d.total
FROM duplicados d
WHERE i.id_inventario = d.conservar;

DELETE FROM inventario a
USING inventario b
WHERE a.id_personaje = b.id_personaje
  AND a.id_item = b.id_item
  AND a.id_inventario > b.id_inventario;

-- Unicidad de las claves externas. PostgreSQL permite varios NULL.
CREATE UNIQUE INDEX IF NOT EXISTS uq_jugador_wow_account
    ON jugador(wow_account_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_personaje_wow_guid
    ON personaje(wow_guid);
CREATE UNIQUE INDEX IF NOT EXISTS uq_item_wow_entry
    ON item(wow_entry);
CREATE UNIQUE INDEX IF NOT EXISTS uq_inventario_personaje_item
    ON inventario(id_personaje, id_item);

-- Índices de apoyo.
CREATE INDEX IF NOT EXISTS idx_personaje_jugador ON personaje(id_jugador);
CREATE INDEX IF NOT EXISTS idx_inventario_personaje ON inventario(id_personaje);
CREATE INDEX IF NOT EXISTS idx_subasta_estado ON subasta(estado);
CREATE INDEX IF NOT EXISTS idx_subasta_fin ON subasta(fecha_fin);
CREATE INDEX IF NOT EXISTS idx_puja_subasta ON puja(id_subasta);
CREATE INDEX IF NOT EXISTS idx_puja_comprador ON puja(id_comprador);
CREATE INDEX IF NOT EXISTS idx_correo_destinatario ON correo(id_destinatario);
