-- ============================================================
-- ProyectoX — Subastas WoW
-- 02_seed.sql: datos iniciales de demostración
-- ============================================================

INSERT INTO jugador (nombre, email, oro) VALUES
    ('Luis',    'luis@example.com',   10000.00),
    ('Aracely', 'aracely@example.com', 5000.00)
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

-- Subasta de ejemplo: Luis vende la Espada de fuego.
-- La CTE solo descuenta el ítem si la subasta se insertó de verdad.
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
