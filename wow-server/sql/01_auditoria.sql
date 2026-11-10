-- Tabla de auditoria usada por la API REST.
-- Ejecutar una sola vez:
--   docker exec -i ac-database mysql -uroot -p"$DOCKER_DB_ROOT_PASSWORD" < sql/01_auditoria.sql

CREATE TABLE IF NOT EXISTS acore_auth.admin_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(64) NOT NULL,
    accion VARCHAR(64) NOT NULL,
    detalle TEXT
);
