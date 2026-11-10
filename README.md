# ProyectoX — Módulo de Subastas WoW (DDD)

Proyecto académico de la clase de Base de Datos. Toma como **guía estructural**
`delivery-monolith` (monolito modular DDD) y lo adapta al dominio de **subastas de
World of Warcraft**. No modifica ni copia el proyecto de delivery: crea un proyecto
nuevo con las mismas capas y los componentes necesarios.

- **Dominio:** subastas de WoW (vendedor, comprador/postor, casa de subastas, correo).
- **Arquitectura:** monolito modular DDD: `domain` → `application` → `infrastructure` → `presentation`.
- **Stack:** Python 3.11, FastAPI, SQLAlchemy 2, PostgreSQL 15, Docker Compose.
- **Modelo ER:** `docs/modelo_er_subastas.drawio` (2 páginas: conceptual y lógico).

---

## Decisiones de alcance (resumen)

| Pregunta | Decisión | Motivo |
|---|---|---|
| ¿PostgreSQL aparte o MySQL integrado al WoW? | **PostgreSQL aparte** | Sigue el molde, aísla el riesgo y permite demostrar sin tocar el servidor WoW. |
| ¿Solo subastas o los 5 módulos? | **Solo subastas + entidades de apoyo** | Es el módulo asignado al grupo; los otros módulos del molde son de delivery. |
| ¿Solo BD, API o todo? | **Todo: BD + API + presentación + documentación** | El molde incluye las 4 capas y la transcripción pide completar módulos. |
| ¿`mod-auctionsim` entra en la entrega? | **Opcional, fuera de la entrega principal** | Es C++ de AzerothCore y requiere recompilar; la entrega se cubre con BD + API. |

Detalle completo en [`docs/decisiones_alcance.md`](docs/decisiones_alcance.md).

---

## Estructura del proyecto

```
proyectoX/
├── README.md
├── .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── init.sql                     # DDL + seed para el contenedor PostgreSQL
├── requirements.txt
├── docs/
│   ├── decisiones_alcance.md    # respuestas a las 4 preguntas
│   ├── modelo_conceptual.md
│   ├── modelo_logico.md
│   ├── modelo_er_subastas.drawio
│   ├── modelo_conceptual_subastas.png
│   ├── modelo_logico_subastas.png
│   ├── modelo_er_subastas.pdf
│   └── reglas_negocio.md
├── sql/
│   ├── 01_schema.sql            # DDL del modelo lógico
│   └── 02_seed.sql              # datos de demostración
├── src/
│   ├── main.py                  # FastAPI + include_router
│   ├── core/
│   │   ├── config.py            # variables de entorno
│   │   └── database.py          # engine, SessionLocal, Base, get_db
│   └── modules/
│       └── auction/
│           ├── domain/
│           │   ├── models.py        # entidades y reglas puras
│           │   ├── repositories.py  # interfaces (contratos)
│           │   └── exceptions.py
│           ├── application/
│           │   ├── dtos.py          # Pydantic entrada/salida
│           │   └── services.py      # casos de uso
│           ├── infrastructure/
│           │   ├── models_db.py     # SQLAlchemy ORM
│           │   └── repository_impl.py
│           └── presentation/
│               └── router.py        # endpoints FastAPI
└── tests/
    └── test_auction.py
```

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

Abre `docs/modelo_er_subastas.drawio` en [diagrams.net](https://app.diagrams.net/)
o en VS Code con la extensión Draw.io. Tiene dos páginas:

1. `modelo conceptual subastas`
2. `modelo logico subastas`

También hay exportaciones listas para revisar:
- `docs/modelo_conceptual_subastas.png`
- `docs/modelo_logico_subastas.png`
- `docs/modelo_er_subastas.pdf` (2 páginas)

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

Las pruebas cubren reglas puras del dominio (duración, pujas, compra directa,
depósito, comisión, cierre y expiración) sin necesitar PostgreSQL.

---

## Notas

- `delivery-monolith` **no se modifica**; solo se usa como referencia de arquitectura.
- El proyecto es independiente del servidor WoW: no toca el MySQL de AzerothCore.
- `mod-auctionsim` es opcional y no forma parte de la entrega principal.
- Si el profesor pide integrar la API con el servidor WoW, se puede cambiar
  `DATABASE_URL` a MySQL y adaptar los repositorios; la estructura DDD no cambia.
