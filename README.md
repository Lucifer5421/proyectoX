# ProyectoX — Módulo de Subastas WoW (DDD)

Proyecto académico de la clase de Base de Datos. Toma como **guía estructural**
`delivery-monolith` (monolito modular DDD) y lo adapta al dominio de **subastas de
World of Warcraft**. No modifica ni copia el proyecto de delivery: crea un proyecto
nuevo con las mismas capas y los componentes necesarios.

- **Dominio:** subastas de WoW (vendedor, comprador/postor, casa de subastas, correo).
- **Arquitectura:** monolito modular DDD: `domain` → `application` → `infrastructure` → `presentation`.
- **Stack:** Python 3.11, FastAPI, SQLAlchemy 2, PostgreSQL 15, Docker Compose.
- **Modelo ER:** `docs/modelo_subastas_2.1.drawio` (2 páginas: conceptual y lógico).

---

## Decisiones de alcance (resumen)

| Pregunta | Decisión | Motivo |
|---|---|---|
| ¿PostgreSQL aparte o MySQL integrado al WoW? | **PostgreSQL aparte** | Sigue el molde, aísla el riesgo y permite demostrar sin tocar el servidor WoW. |
| ¿Solo subastas o varios módulos? | **Cuatro módulos: `auth`, `inventory`, `auction`, `finance`** | El modelo 2.1 separa cuentas, inventario, subastas y finanzas; el dominio sigue siendo subastas. |
| ¿Solo BD, API o todo? | **Todo: BD + API + presentación + documentación** | El molde incluye las 4 capas y la transcripción pide completar módulos. |
| ¿`mod-auctionsim` entra en la entrega? | **Opcional, fuera de la entrega principal** | Es C++ de AzerothCore y requiere recompilar; la entrega se cubre con BD + API. |

Detalle completo en [`docs/decisiones_alcance.md`](docs/decisiones_alcance.md).

---

## Estructura del proyecto

```
proyectoX/
├── README.md
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── init.sql                     # DDL + seed para el contenedor PostgreSQL
├── requirements.txt
├── docs/
│   ├── decisiones_alcance.md    # respuestas a las 4 preguntas
│   ├── modelo_conceptual.md
│   ├── modelo_logico.md
│   ├── modelo_subastas_2.1.drawio
│   ├── modelo_conceptual_subastas.png
│   ├── modelo_logico_subastas.png
│   ├── modelo_subastas_2.1.pdf
│   ├── integracion_wow.md       # sync de solo lectura con AzerothCore
│   ├── estructura_modulos.md    # mapeo delivery -> proyectoX y capas DDD
│   └── reglas_negocio.md
├── sql/
│   ├── 01_schema.sql            # DDL del modelo lógico 2.1
│   ├── 02_seed.sql              # datos de demostración
│   └── 03_integracion_wow.sql   # migración del modelo 2.1 + claves WoW
├── src/
│   ├── main.py                  # FastAPI + include_router
│   ├── core/
│   │   ├── config.py            # variables de entorno
│   │   └── database.py          # engine, SessionLocal, Base, get_db
│   ├── integrations/
│   │   └── wow/
│   │       ├── config.py        # credenciales/URL del sync
│   │       ├── client.py        # MySQL de AzerothCore (solo lectura)
│   │       ├── mapping.py       # filas WoW -> dominio de subastas
│   │       └── sync.py          # CLI de sincronización
│   └── modules/
│       ├── auth/                # jugador, personaje y oro del personaje
│       │   ├── domain/
│       │   │   ├── exceptions.py
│       │   │   ├── models.py
│       │   │   └── repositories.py
│       │   ├── application/
│       │   │   ├── datos.py
│       │   │   └── services.py
│       │   ├── infrastructure/
│       │   │   ├── external_adapter.py
│       │   │   ├── models_db.py
│       │   │   └── repositories_impl.py
│       │   └── presentation/
│       │       ├── routers.py
│       │       └── schemas.py
│       ├── inventory/           # item e inventario personaje-ítem
│       │   ├── domain/
│       │   │   ├── exceptions.py
│       │   │   ├── models.py
│       │   │   └── repositories.py
│       │   ├── application/
│       │   │   ├── datos.py
│       │   │   └── services.py
│       │   ├── infrastructure/
│       │   │   ├── external_adapter.py
│       │   │   ├── models_db.py
│       │   │   └── repositories_impl.py
│       │   └── presentation/
│       │       ├── routers.py
│       │       └── schemas.py
│       ├── auction/             # subasta y puja
│       │   ├── domain/
│       │   │   ├── exceptions.py
│       │   │   ├── models.py
│       │   │   └── repositories.py
│       │   ├── application/
│       │   │   ├── datos.py
│       │   │   └── services.py
│       │   ├── infrastructure/
│       │   │   ├── external_adapter.py
│       │   │   ├── models_db.py
│       │   │   └── repositories_impl.py
│       │   └── presentation/
│       │       ├── routers.py
│       │       └── schemas.py
│       └── finance/             # depósito, comisión, transacción y correo
│           ├── domain/
│           │   ├── exceptions.py
│           │   ├── models.py
│           │   └── repositories.py
│           ├── application/
│           │   ├── datos.py
│           │   └── services.py
│           ├── infrastructure/
│           │   ├── external_adapter.py
│           │   ├── models_db.py
│           │   └── repositories_impl.py
│           └── presentation/
│               ├── routers.py
│               └── schemas.py
├── tests/
│   ├── test_auction.py
│   ├── test_modules.py
│   ├── test_structure.py
│   └── test_wow_sync.py
└── wow-server/                  # stack WoW custom (sanitizado)
    ├── README.md
    ├── docker-compose.yml
    ├── .env.example
    ├── api/
    ├── scripts/
    ├── systemd/
    ├── sql/
    └── docs/
```

Todos los módulos respetan la misma estructura de capas: `domain`,
`application`, `infrastructure` y `presentation`. El mapeo desde los módulos
de `delivery-monolith` (incluido `restaurant` → `inventory`) y las reglas de
dependencia están en
[`docs/estructura_modulos.md`](docs/estructura_modulos.md).

---

## Cómo ejecutar

### Requisitos
- Docker y Docker Compose.

### 1. Levantar PostgreSQL + API

```bash
cd ~/Documentos/proyectoX
cp .env.example .env   # solo si no existe .env
docker compose up -d --build
```

La API queda en `http://localhost:8002` y Swagger en
`http://localhost:8002/docs`.

### 2. Verificar

```bash
docker compose ps
curl http://localhost:8002/
```

### 3. Detener

```bash
docker compose down          # conserva el volumen
docker compose down -v       # borra también la base de datos
```

> El contenedor PostgreSQL usa el puerto **5433** en el host para no chocar con
> otros PostgreSQL. La API usa el puerto **8002** para no chocar con la API del
> servidor WoW (8001).

---

## Integración con el servidor WoW

El servidor de WoW (AzerothCore + Docker + Tailscale + API) está en
[`wow-server/`](wow-server/README.md). Es una copia **sanitizada** del montaje
real: no incluye el código fuente oficial de AzerothCore (se clona con
`wow-server/scripts/setup-wow-server.sh`) ni contraseñas.

La API de subastas **sigue usando PostgreSQL** y no se conecta a WoW en tiempo
de ejecución. La integración es un CLI de **solo lectura**:

```bash
# 1. Ten el stack WoW y su API configurados (wow-server/api/.env).
# 2. Añade DATABASE_URL_LOCAL en .env (ver .env.example).
# 3. Sincroniza:
wow-server/scripts/sync-wow.sh --dry-run   # ver qué haría
wow-server/scripts/sync-wow.sh             # personajes + ítems + oro real
wow-server/scripts/sync-wow.sh --skip-gold # conserva el oro de la demo
```

El sync copia cuentas y personajes (con su oro) e inventario reales a
`jugador`, `personaje`, `item` e `inventario`. **Nunca escribe en `acore_*`.**
El oro vive en `personaje`, no en `jugador`, tal como indica el modelo 2.1.
Detalle completo en [`docs/integracion_wow.md`](docs/integracion_wow.md).

> Para una base ya creada, aplica la migración:
> `docker exec -i proyectoX-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < sql/03_integracion_wow.sql`

---

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auctions/` | Publicar una subasta. |
| `GET` | `/auctions/` | Listar subastas activas. |
| `GET` | `/auctions/{id}` | Detalle de una subasta. |
| `POST` | `/auctions/{id}/bids` | Pujar. |
| `GET` | `/auctions/{id}/bids` | Listar pujas de una subasta. |
| `POST` | `/auctions/{id}/buy` | Compra directa. |
| `POST` | `/auctions/{id}/close` | Cerrar/expirar una subasta vencida. |
| `GET` | `/auth/players` | Listar cuentas de jugador. |
| `GET` | `/auth/characters` | Listar personajes y su oro. |
| `GET` | `/auth/characters/{id}` | Detalle de un personaje. |
| `GET` | `/inventory/items` | Listar el catálogo de ítems. |
| `GET` | `/inventory/characters/{id}` | Inventario de un personaje. |
| `GET` | `/mail/{id_personaje}` | Correo de un personaje. |
| `GET` | `/` | Health check. |

### Ejemplos

Publicar (Luis vende Tela de lino, ítem 3; el seed deja 5 unidades):

```bash
curl -X POST http://localhost:8002/auctions/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_vendedor": 1,
    "id_item": 3,
    "precio_salida": 10,
    "precio_compra_directa": 25,
    "duracion_horas": 24,
    "cantidad": 1
  }'
```

> La subasta de ejemplo del seed es la `1` (Luis vende la Espada de fuego).
> Puedes pujar o comprar directamente sobre ella con Aracely (`id_comprador: 2`).

Pujar (Aracely ofrece 120):

```bash
curl -X POST http://localhost:8002/auctions/1/bids \
  -H "Content-Type: application/json" \
  -d '{"id_comprador": 2, "monto": 120}'
```

Compra directa:

```bash
curl -X POST http://localhost:8002/auctions/1/buy \
  -H "Content-Type: application/json" \
  -d '{"id_comprador": 2}'
```

Listar correo:

```bash
curl http://localhost:8002/mail/2
```

> Los IDs de ejemplo (`1`, `2`) corresponden a los datos del seed. Si ya creaste
> registros, consulta los IDs reales en PostgreSQL.

---

## Modelo ER

- **Conceptual:** entidades, atributos y relaciones con cardinalidades.
- **Lógico:** tablas, PK/FK, tipos y restricciones.

Abre `docs/modelo_subastas_2.1.drawio` en [diagrams.net](https://app.diagrams.net/)
o en VS Code con la extensión Draw.io. Tiene dos páginas:

1. `modelo conceptual subastas`
2. `modelo logico subastas`

El modelo 2.1 se refleja en los cuatro módulos: `auth` (`jugador`,
`personaje`), `inventory` (`item`, `inventario`), `auction` (`subasta`,
`puja`) y `finance` (`deposito`, `comision`, `transaccion`, `correo`).
`jugador` no guarda oro (vive en `personaje`), `personaje.nombre` es único,
`transaccion` no repite `id_vendedor` (se deduce de `subasta`) y
`correo.estado` usa `pendiente`, `leido`, `cobrado` o `devuelto`.

También hay exportaciones listas para revisar:
- `docs/modelo_conceptual_subastas.png`
- `docs/modelo_logico_subastas.png`
- `docs/modelo_subastas_2.1.pdf` (2 páginas)

Versiones de lectura rápida en:
- [`docs/modelo_conceptual.md`](docs/modelo_conceptual.md)
- [`docs/modelo_logico.md`](docs/modelo_logico.md)

---

## Reglas de negocio implementadas

- Depósito del **5%** del precio de salida al publicar.
- Duraciones permitidas: **2, 8 o 24 horas**.
- La puja debe superar la puja actual.
- El oro de la puja se retiene; si el postor es superado, se reembolsa.
- Compra directa cierra la subasta y entrega el ítem por correo.
- Al vencer: gana la puja más alta; el vendedor recibe el monto menos el **5%** de comisión.
- Sin pujas al vencer: la subasta expira y el ítem se devuelve al vendedor por correo.
- El ítem queda retenido por la casa de subastas mientras la subasta está activa.

Detalle en [`docs/reglas_negocio.md`](docs/reglas_negocio.md).

---

## Pruebas

```bash
cd ~/Documentos/proyectoX
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Las 24 pruebas cubren reglas puras del dominio (duración, pujas, compra
directa, depósito, comisión, cierre y expiración), las entidades de
`auth`/`inventory`/`finance` (`tests/test_modules.py`), el
mapeo/sincronización de WoW (`tests/test_wow_sync.py`) y la estructura
modular exigida (`tests/test_structure.py`), sin necesitar PostgreSQL ni
MySQL.

---

## Notas

- `delivery-monolith` **no se modifica**; solo se usa como referencia de arquitectura.
- La API de subastas es independiente en runtime: usa PostgreSQL y no toca el
  MySQL de AzerothCore. La integración es un CLI de solo lectura
  (`wow-server/scripts/sync-wow.sh`).
- `wow-server/` contiene la copia sanitizada del stack WoW custom; el clon
  oficial de AzerothCore no se publica (se obtiene con
  `wow-server/scripts/setup-wow-server.sh`).
- `wow_account_id`, `wow_guid` y `wow_entry` son columnas técnicas de la
  integración de solo lectura; no forman parte del modelo lógico 2.1.
- `mod-auctionsim` es opcional y no forma parte de la entrega principal.
- Para que las subastas entreguen ítems dentro del juego haría falta SOAP o
  `mod-auctionsim`; la entrega actual cubre BD + API + documentación + sync.
