# ProyectoX — Sistema de subastas para WoW Classic

**Informe técnico — Módulo de Base de Datos**

---

## Resumen ejecutivo

ProyectoX implementa un sistema de subastas inspirado en la casa de subastas de
*World of Warcraft Classic*. El trabajo toma como fuente de verdad el **modelo
lógico 2.1** (`docs/modelo_subastas_2.1.drawio`) y como guía funcional el video
de la clase
[¿Cómo comprar y vender en la casa de subastas? WoW Classic](https://youtu.be/cNxya6UBwAo)
(dracdargent), que describe la publicación, la búsqueda, las pujas, la
compra directa, el correo y la cancelación de subastas.

La solución se construye como un **monolito modular con arquitectura DDD**:
cinco módulos de dominio, diez tablas en PostgreSQL y una API REST que expone
los casos de uso. El servidor de WoW queda aislado: la integración es una
herramienta de línea de comandos de solo lectura.

| Aspecto | Implementación |
|---|---|
| Objetivo | Gestionar subastas de ítems entre personajes de WoW |
| Dominio | Jugador, personaje, ítem, inventario, subasta, puja, depósito, comisión, transacción y correo |
| Arquitectura | Monolito modular DDD (`domain` → `application` → `infrastructure` → `presentation`) |
| Modelo | Conceptual, lógico y de módulos en `docs/modelo_subastas_2.1.drawio` (3 páginas) |
| Base de datos | PostgreSQL 15 con DDL puro en `init.sql` |
| API | FastAPI en `http://localhost:8002`; documentación interactiva en `/docs` |
| Stack | Python 3.11, FastAPI, SQLAlchemy 2, PostgreSQL 15, Docker Compose |
| Entregable | Base de datos, API, documentación técnica y pruebas automatizadas |

---

## 1. Alcance y decisiones de diseño

| Decisión | Resultado | Justificación |
|---|---|---|
| Motor de datos | PostgreSQL en contenedor propio | Aísla el riesgo, permite demostrar el sistema sin modificar la base de datos del juego. |
| Organización | Cinco módulos del modelo 2.1: `auth`, `inventory`, `auction`, `finance` y `mail` | Los nombres corresponden a responsabilidades del dominio de subastas, no a nombres prestados. |
| Cobertura | Base de datos + API + presentación + documentación | Las cuatro capas DDD forman parte del objetivo académico; entregar solo SQL dejaría fuera la API. |
| Integración con WoW | Opcional y de solo lectura | `mod-auctionsim` requiere recompilar AzerothCore y no es necesario para la entrega. |

El detalle de cada decisión está en
[`docs/decisiones_alcance.md`](docs/decisiones_alcance.md).

---

## 2. Arquitectura y módulos

```text
FastAPI (presentation)
        ↓
Casos de uso (application)
        ↓
Entidades y reglas (domain)
        ↓
Repositorios y ORM (infrastructure)
        ↓
PostgreSQL
```

| Módulo | Tablas del modelo 2.1 | Responsabilidad | Superficie pública |
|---|---|---|---|
| `auth` | `jugador`, `personaje` | Cuentas, personajes y oro disponible | `/auth` |
| `inventory` | `item`, `inventario` | Catálogo de objetos y existencias por personaje | `/inventory` |
| `auction` | `subasta`, `puja` | Publicación, pujas, compra directa, cierre y cancelación | `/auctions` |
| `finance` | `deposito`, `comision`, `transaccion` | Depósitos, comisiones y movimientos de oro | Módulo interno, sin endpoints |
| `mail` | `correo` | Buzón interno del personaje | `/mail` |

`finance` no expone API: `AuctionService` invoca a `FinanceService` al publicar,
pujar, comprar o cerrar una subasta. La comunicación entre módulos se realiza
siempre a través de servicios de aplicación.

**Persistencia.** El esquema físico se define en SQL en `init.sql`. SQLAlchemy
se utiliza en la capa de infraestructura: `models_db.py` mapea cada tabla a una
clase Python y `repository_impl.py` ejecuta las consultas mediante una sesión.
El dominio y la capa de aplicación no dependen de SQLAlchemy ni de FastAPI.

---

## 3. Mapa rápido del código

Todos los archivos Python de `src/` comienzan con una cabecera de cinco líneas:

```python
# ============================================================================
# MÓDULO: auction  |  CAPA: domain  |  ARCHIVO: models.py
# QUÉ HACE: Entidades y reglas de negocio puras del módulo de subastas.
# DETALLE: clases: EstadoSubasta, EstadoPuja, Puja, Subasta
# ============================================================================
```

- **MÓDULO**: `auth`, `inventory`, `auction`, `finance` o `mail`. También
  aparecen `core` (configuración y base de datos), `integraciones/wow` y
  `aplicación` (`src/main.py`).
- **CAPA**: `domain`, `application`, `infrastructure`, `presentation`, además
  de `base`, `integración` y `composición`.
- **QUÉ HACE**: función del archivo en una frase.
- **DETALLE**: entidades, clases, funciones o endpoints que contiene.

Los archivos SQL usan el mismo esquema en comentarios `-- MÓDULO ...` y
`-- QUÉ HACE: ...`. La leyenda completa está en
[`docs/estructura_modulos.md`](docs/estructura_modulos.md).

---

## 4. Estructura del proyecto

```text
proyectoX/
├── README.md
├── .env.example                 # plantilla de configuración (sin secretos)
├── docker-compose.yml
├── Dockerfile
├── init.sql                     # DDL puro del modelo 2.1
├── requirements.txt
├── docs/
│   ├── decisiones_alcance.md
│   ├── estructura_modulos.md
│   ├── integracion_wow.md
│   ├── modelo_conceptual.md
│   ├── modelo_logico.md
│   ├── modelo_subastas_2.1.drawio
│   ├── modelo_subastas_2.1.pdf
│   ├── modelo_conceptual_subastas.png
│   ├── modelo_logico_subastas.png
│   └── reglas_negocio.md
├── sql/
│   ├── 01_schema.sql            # copia manual de init.sql
│   ├── 02_seed.sql              # datos de demostración
│   └── 03_integracion_wow.sql   # migración y claves técnicas de WoW
├── src/
│   ├── main.py                  # composición de la API
│   ├── core/                    # configuración y sesión de base de datos
│   ├── integrations/wow/        # sincronización de solo lectura
│   └── modules/
│       ├── auth/                # jugador, personaje
│       │   ├── application/     # servicios y DTOs (+ casos_uso-orquestacion.txt)
│       │   ├── domain/          # entidades y reglas (+ reglas_negocio.txt)
│       │   ├── infrastructure/  # ORM, repositorios (+ implementacion_tecnica.txt)
│       │   └── presentation/    # router (+ capa_exposicion.txt)
│       ├── inventory/           # item, inventario
│       │   ├── application/
│       │   ├── domain/
│       │   ├── infrastructure/
│       │   └── presentation/
│       ├── auction/             # subasta, puja
│       │   ├── application/
│       │   ├── domain/
│       │   ├── infrastructure/
│       │   └── presentation/
│       ├── finance/             # depósito, comisión, transacción
│       │   ├── application/
│       │   ├── domain/
│       │   └── infrastructure/  # sin presentation: módulo interno
│       └── mail/                # correo
│           ├── application/
│           ├── domain/
│           ├── infrastructure/
│           └── presentation/
├── tests/                       # 40 pruebas en 4 archivos + __init__.py
│   ├── test_auction.py
│   ├── test_modules.py
│   ├── test_structure.py
│   └── test_wow_sync.py
└── wow-server/                  # stack WoW de prueba, sin credenciales
```

Cada archivo lleva una cabecera `MÓDULO / CAPA / ARCHIVO / QUÉ HACE / DETALLE`,
explicada en la sección 3; el inventario completo está en
[`docs/estructura_modulos.md`](docs/estructura_modulos.md). `finance` no tiene
`presentation/` porque no expone endpoints. `auth` conserva cuatro documentos
`.txt` de apoyo: casos de uso, reglas de negocio, implementación técnica y
exposición de la capa de presentación.

---

## 5. Modelo de datos

Las diez tablas del modelo lógico 2.1 están repartidas entre los cinco módulos:

```text
JUGADOR (1) ──< (N) PERSONAJE
PERSONAJE (N) ──< INVENTARIO >── (M) ITEM
PERSONAJE (1) ──< (N) SUBASTA
ITEM (1) ──< (N) SUBASTA
SUBASTA (1) ──< (N) PUJA
PERSONAJE (1) ──< (N) PUJA
SUBASTA (1) ── (1) TRANSACCION
SUBASTA (1) ── (1) DEPOSITO
SUBASTA (1) ── (1) COMISION
PERSONAJE (1) ──< (N) CORREO
ITEM (1) ──< (N) CORREO
```

Decisiones relevantes del modelo:

- El oro pertenece a `personaje`, no a `jugador`.
- `personaje.nombre` es único.
- `transaccion` no repite `id_vendedor`: se deduce de `subasta`.
- `correo.estado` usa `pendiente`, `leido`, `cobrado` o `devuelto`.
- Cada bloque del DDL documenta módulo, PK, FK, cardinalidad y restricciones.

`wow_account_id`, `wow_guid` y `wow_entry` son columnas técnicas de la
integración con AzerothCore; no forman parte del modelo lógico 2.1.

Para abrir el diagrama, usa [diagrams.net](https://app.diagrams.net/) con
`docs/modelo_subastas_2.1.drawio`. Sus tres páginas son `modelo conceptual
subastas`, `modelo logico subastas` y `modulos`. También hay exportaciones en
PNG y PDF. Las versiones de lectura rápida son
[`docs/modelo_conceptual.md`](docs/modelo_conceptual.md) y
[`docs/modelo_logico.md`](docs/modelo_logico.md).

---

## 6. Reglas de negocio implementadas

- Depósito del **5 %** del precio de salida al publicar.
- Duraciones permitidas: **2, 8 o 24 horas**.
- Cada puja debe superar la actual en al menos **0.01** (1 cobre).
- El oro de la puja se retiene y se reembolsa al postor superado.
- La compra directa cierra la subasta y entrega el ítem por correo.
- Al vencer, gana la puja más alta; el vendedor recibe el importe menos la
  comisión del **5 %**. Sin pujas, la subasta expira y el ítem se devuelve.
- El vendedor puede cancelar una subasta activa: se reembolsan las pujas y el
  ítem vuelve a su inventario.
- El correo de una compra registra el importe pagado en `oro` y en el asunto.
- `item.precio_base` equivale al “precio del vendedor” mostrado en la guía.
- `GET /auctions/` admite búsqueda por nombre (`q`), filtros por vendedor,
  comprador y objetos utilizables según el nivel del personaje, y orden por
  precio, rareza, nivel, tiempo restante o vendedor.
- Cada subasta expone `id_ganador_actual` y `tiempo_restante` en segundos.
- El ítem permanece retenido mientras la subasta está activa.

El listado completo está en [`docs/reglas_negocio.md`](docs/reglas_negocio.md).

---

## 7. API REST

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auctions/` | Publicar una subasta. |
| `GET` | `/auctions/` | Listar activas; admite `q`, `id_vendedor`, `id_comprador`, `id_personaje`, `usable` y `sort`. |
| `GET` | `/auctions/{id}` | Detalle de una subasta. |
| `POST` | `/auctions/{id}/bids` | Pujar (mínimo +0.01 sobre la puja actual). |
| `GET` | `/auctions/{id}/bids` | Listar pujas; admite `id_comprador`. |
| `POST` | `/auctions/{id}/buy` | Compra directa. |
| `POST` | `/auctions/{id}/close` | Cerrar una subasta vencida. |
| `POST` | `/auctions/{id}/cancel` | Cancelar una subasta propia (cuerpo: `id_vendedor`). |
| `GET` | `/auth/players` | Listar cuentas de jugador. |
| `GET` | `/auth/characters` | Listar personajes y su oro. |
| `GET` | `/auth/characters/{id}` | Detalle de un personaje. |
| `GET` | `/inventory/items` | Listar el catálogo de ítems. |
| `GET` | `/inventory/characters/{id}` | Inventario de un personaje. |
| `GET` | `/mail/{id_personaje}` | Correo de un personaje. |
| `GET` | `/` | Verificación de estado. |

Valores aceptados en `sort`: `precio_asc`, `precio_desc`, `rareza`, `nivel`,
`tiempo` y `vendedor`. Para filtrar objetos utilizables se requiere
`usable=true` junto con `id_personaje`.

### Ejemplos

Publicar una subasta (Luis vende Tela de lino, ítem 3):

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

Buscar y ordenar:

```bash
curl "http://localhost:8002/auctions/?q=espada&sort=precio_asc"
curl "http://localhost:8002/auctions/?usable=true&id_personaje=1"
```

Pujar y comprar:

```bash
curl -X POST http://localhost:8002/auctions/1/bids \
  -H "Content-Type: application/json" \
  -d '{"id_comprador": 2, "monto": 120}'

curl -X POST http://localhost:8002/auctions/1/buy \
  -H "Content-Type: application/json" \
  -d '{"id_comprador": 2}'
```

Consultar el correo del comprador:

```bash
curl http://localhost:8002/mail/2
```

Los identificadores `1` y `2` corresponden a los datos de demostración. Si la
base ya contiene otros registros, consulta los identificadores reales antes de
ejecutar los ejemplos.

---

## 8. Puesta en marcha

### Requisitos

- Docker y Docker Compose.

### Arranque

```bash
cd proyectoX
cp .env.example .env   # solo si no existe .env
docker compose up -d --build
```

La API queda disponible en `http://localhost:8002` y Swagger en
`http://localhost:8002/docs`.

En el primer arranque, PostgreSQL ejecuta `init.sql` (solo DDL) y después
`sql/02_seed.sql` (datos de demostración). Si el volumen ya existe, estos
archivos no se vuelven a ejecutar.

### Verificación y parada

```bash
docker compose ps
curl http://localhost:8002/

docker compose down          # conserva el volumen
docker compose down -v       # elimina también la base de datos
```

El contenedor de PostgreSQL usa el puerto **5433** en el host y la API el
**8002**, para no interferir con otros servicios.

---

## 9. Pruebas y validación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

La suite contiene **40 pruebas** y cubre:

- Reglas puras del dominio: duración, pujas, incremento mínimo, ganador actual,
  tiempo restante, cancelación, compra directa, depósito, comisión, cierre y
  expiración (`tests/test_auction.py`).
- Entidades de los cinco módulos (`tests/test_modules.py`).
- Estructura modular y pureza del DDL (`tests/test_structure.py`).
- Mapeo y sincronización de datos de WoW (`tests/test_wow_sync.py`).

Las pruebas no requieren PostgreSQL ni MySQL. Como validación adicional se
comprobó la compilación de los módulos, la carga del DDL y del seed en una base
temporal, y las respuestas HTTP de los endpoints.

---

## 10. Integración con el servidor WoW

El servidor de prueba (AzerothCore + Docker + Tailscale + API) está documentado
en [`wow-server/README.md`](wow-server/README.md). Es una copia sin
credenciales: el código oficial de AzerothCore se obtiene con
`wow-server/scripts/setup-wow-server.sh`.

La API de subastas usa PostgreSQL y **no se conecta a WoW en tiempo de
ejecución**. La integración es un CLI de solo lectura que copia cuentas,
personajes, oro, ítems e inventario reales:

```bash
wow-server/scripts/sync-wow.sh --dry-run   # simular la operación
wow-server/scripts/sync-wow.sh             # aplicar la sincronización
wow-server/scripts/sync-wow.sh --skip-gold # conservar el oro de la demostración
```

El proceso nunca escribe en las tablas `acore_*`. Para una base ya creada,
aplica la migración:

```bash
docker exec -i proyectoX-db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < sql/03_integracion_wow.sql
```

Detalle completo en [`docs/integracion_wow.md`](docs/integracion_wow.md).

---

## 11. Aclaraciones técnicas

- **No se envían correos electrónicos.** El módulo `mail` representa el buzón
  interno del juego: inserta filas en `correo` para el `id_destinatario`. No hay
  SMTP ni notificaciones externas; `jugador.email` es únicamente un
  identificador único de la cuenta.
- **`.env.example`** es la plantilla de configuración de Docker. Se copia a
  `.env` (ignorado por Git), no contiene secretos ni direcciones de correo y
  debe conservarse en el repositorio para documentar las variables.
- **`origin`** es la URL de Git (`https://github.com/Lucifer5421/proyectoX.git`),
  utilizada solo por `git push` y `git pull`. No contiene credenciales; la
  autenticación se gestiona con `gh`.
- **`mod-auctionsim`** es un complemento opcional de AzerothCore. La entrega
  actual cubre base de datos, API, documentación y sincronización de solo
  lectura; la entrega de objetos dentro del cliente requeriría este módulo o
  una integración SOAP.

---

## 12. Referencias

1. **Guía funcional de la casa de subastas:**
   [¿Cómo comprar y vender en la casa de subastas? WoW Classic](https://youtu.be/cNxya6UBwAo),
   dracdargent. Video tomado como guía de la clase para identificar los casos
   de uso de búsqueda, publicación, pujas, compra, correo y cancelación.
2. **Modelo lógico 2.1:** `docs/modelo_subastas_2.1.drawio` y su exportación en
   `docs/modelo_subastas_2.1.pdf`. Fuente de verdad de entidades, relaciones y
   asignación a módulos.
3. **Material de la clase:** transcripción de la sesión, documento de
   observaciones y sugerencias del ingeniero, y documento de actores de WoW.
4. **Documentación interna:** [estructura de módulos](docs/estructura_modulos.md),
   [reglas de negocio](docs/reglas_negocio.md),
   [decisiones de alcance](docs/decisiones_alcance.md) e
   [integración con WoW](docs/integracion_wow.md).
