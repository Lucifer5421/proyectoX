-- Consultas de ejemplo para la parte de base de datos del proyecto.
-- Conectarse con: mysql -h 127.0.0.1 -P 3307 -u acore_api -p

-- 1. Cuentas y nivel GM
SELECT a.id, a.username, COALESCE(aa.gmlevel, 0) AS gmlevel, a.last_login
FROM acore_auth.account a
LEFT JOIN acore_auth.account_access aa ON aa.id = a.id
ORDER BY a.id;

-- 2. Personajes con nivel y oro (money esta en cobre)
SELECT guid, account, name, level,
       money,
       ROUND(money / 10000, 2) AS oro,
       online
FROM acore_characters.characters
ORDER BY guid;

-- 3. Subir un personaje a nivel 80
UPDATE acore_characters.characters
SET level = 80
WHERE name = 'NombreDelPersonaje';

-- 4. Dar 1000 de oro (1000 * 10000 cobre)
UPDATE acore_characters.characters
SET money = 1000 * 10000
WHERE name = 'NombreDelPersonaje';

-- 5. Ver los NPC creados en el mundo
SELECT guid, id, map, position_x, position_y, position_z
FROM acore_world.creature
ORDER BY guid DESC
LIMIT 20;

-- 6. Ver la plantilla de un NPC
SELECT entry, name, subname, minlevel, maxlevel, faction
FROM acore_world.creature_template
WHERE entry = 12345;

-- 7. Configuracion del reino (IP que recibe el cliente)
SELECT id, name, address, localAddress, port, gamebuild
FROM acore_auth.realmlist;

-- 8. Eliminar una cuenta y sus personajes (ejemplo)
--    Primero personajes, luego permisos, luego la cuenta.
DELETE FROM acore_characters.characters
WHERE account = (SELECT id FROM acore_auth.account WHERE username = 'USUARIO');

DELETE FROM acore_auth.account_access
WHERE id = (SELECT id FROM acore_auth.account WHERE username = 'USUARIO');

DELETE FROM acore_auth.account
WHERE username = 'USUARIO';

-- 9. Historial de cambios hechos por la API
SELECT id, fecha, usuario, accion, detalle
FROM acore_auth.admin_audit
ORDER BY id DESC
LIMIT 50;
