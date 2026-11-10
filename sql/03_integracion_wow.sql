-- ============================================================
-- ProyectoX — 03_integracion_wow.sql
-- Claves externas de AzerothCore para la sincronización de solo lectura.
--
-- Ejecutar una vez sobre una base ya existente:
--   docker exec -i proyectoX-db sh -c \
--     'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
--     < sql/03_integracion_wow.sql
--
-- En una instalación nueva, init.sql / 01_schema.sql ya incluyen
-- estas columnas y restricciones.
-- ============================================================

ALTER TABLE jugador   ADD COLUMN IF NOT EXISTS wow_account_id INTEGER;
ALTER TABLE personaje ADD COLUMN IF NOT EXISTS wow_guid INTEGER;
ALTER TABLE item      ADD COLUMN IF NOT EXISTS wow_entry INTEGER;

-- Los nombres de ítem de WoW pueden superar los 100 caracteres.
ALTER TABLE item ALTER COLUMN nombre TYPE VARCHAR(255);

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
