# Integración con el servidor WoW (AzerothCore)

`proyectoX` sigue siendo un **monolito modular DDD con PostgreSQL propio**.
La integración con el servidor de World of Warcraft es **opcional y de solo
lectura**: un comando copia personajes, oro e inventario reales desde el MySQL
de AzerothCore hacia las tablas de apoyo de subastas.

```
AzerothCore MySQL (127.0.0.1:3307)
  acore_auth.account
  acore_characters.characters
  acore_characters.character_inventory
  acore_characters.item_instance
  acore_world.item_template
            |
            |  SELECT (solo lectura)
            v
  src/integrations/wow/sync.py
            |
            |  INSERT/UPDATE
            v
proyectoX PostgreSQL (localhost:5433)
  jugador, personaje, item, inventario
```

## Qué se sincroniza

| Origen AzerothCore | Destino proyectoX | Regla |
|---|---|---|
| `acore_auth.account` | `jugador.wow_account_id` | Cuenta del jugador. |
| `acore_characters.characters` | `personaje` | GUID, nombre, nivel, clase y oro. |
| `characters.money` | `personaje.oro` | Cobre / 10 000 = oro. |
| `item_template` | `item` | `entry` como `wow_entry`, nombre, calidad, nivel y precio. |
| `character_inventory` + `item_instance` | `inventario` | Cantidad sumada por personaje e ítem. |

En el código, `jugador` y `personaje` pertenecen al módulo `auth`; `item` e
`inventario` pertenecen a `inventory`. El sync no modifica las tablas de
`auction` ni de `finance`.

Columnas nuevas (ver `sql/03_integracion_wow.sql`):

- `jugador.wow_account_id` — cuenta de AzerothCore (UNIQUE).
- `personaje.wow_guid` — GUID del personaje (UNIQUE).
- `item.wow_entry` — entry de `item_template` (UNIQUE).
- `inventario (id_personaje, id_item)` — UNIQUE para hacer upsert.

## Cómo ejecutarlo

1. Ten el stack WoW levantado y la API configurada:

   ```bash
   ls wow-server/api/.env          # debe existir
   docker ps | grep ac-database
   ```

2. Asegúrate de tener `DATABASE_URL_LOCAL` en `proyectoX/.env`:

   ```env
   DATABASE_URL_LOCAL=postgresql+psycopg2://wow_auction_user:wow_auction_password@localhost:5433/wow_auctions
   ```

3. Instala dependencias en el virtualenv del proyecto:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Prueba primero sin escribir:

   ```bash
   wow-server/scripts/sync-wow.sh --dry-run
   ```

5. Aplica la sincronización:

   ```bash
   wow-server/scripts/sync-wow.sh
   ```

   Para conservar el oro de la demo (Luis 9995, Aracely 5000) y sincronizar
   solo personajes/ítems:

   ```bash
   wow-server/scripts/sync-wow.sh --skip-gold
   ```

## Ejemplo real del servidor

Al momento de la integración, AzerothCore tenía:

| Personaje | GUID | Nivel | Clase | Oro real |
|---|---|---|---|---|
| Luis | 1 | 80 | Pícaro | 2000.00 |
| Luci | 2 | 1 | Chamán | 0.00 |
| Aracely | 3 | 1 | Mago | 0.00 |

El inventario real incluía `Footpad's Shirt`, `Worn Dagger`, `Hearthstone`,
`Primitive Mantle`, `Apprentice's Robe`, etc. El sync los inserta como ítems
nuevos (`wow_entry`) y no borra los ítems de demostración del seed.

## Limitaciones y decisiones

- **No hay escritura hacia WoW.** El sync nunca modifica `acore_auth`,
  `acore_characters` ni `acore_world`. Si se vende un ítem en la API de
  subastas, el ítem no aparece dentro del juego.
- **El oro se puede preservar.** `--skip-gold` deja el oro de la demo para que
  las pruebas de puja/compra sigan funcionando. Sin el flag, el oro de
  `personaje` se reemplaza por el oro real de WoW.
- **No se instala `mod-auctionsim`.** Es C++ de AzerothCore y requiere
  recompilar el worldserver. Queda como trabajo opcional.
- **La API de subastas no se conecta a WoW en runtime.** Sigue usando
  PostgreSQL; el sync es un proceso aparte que se ejecuta cuando se quiere
  refrescar los datos. Esto mantiene el aislamiento y evita que una subasta
  dañe la base del juego.
- **El stack WoW vive en `wow-server/`.** Es una copia sanitizada del montaje
  real; el servidor en ejecución en `~/preyecro_docker` no se toca.

## Pruebas

```bash
pytest -q
```

Las pruebas de `tests/test_wow_sync.py` cubren:

- Conversión de cobre a oro.
- Nombres de clase y rareza.
- Truncado de nombres largos.
- Deduplicación de ítems repetidos (Hearthstone).
- Plan de 3 cuentas/personajes y 7 filas de inventario.

No necesitan MySQL ni PostgreSQL.
