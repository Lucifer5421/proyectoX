# Estructura modular de proyectoX

Este documento fija la estructura de `proyectoX` a partir del **modelo lógico
2.1** (`docs/modelo_subastas_2.1.drawio`) y de la organización por capas de
`delivery-monolith`.

`delivery-monolith` se usa **solo como referencia de arquitectura**: no se
modifica y ya no se copian sus nombres de módulos. Los módulos de proyectoX
son los del dominio de subastas de World of Warcraft.

## 1. Módulos

```text
src/modules/
├── auth/        # jugador y personaje
├── inventory/   # item e inventario
├── auction/     # subasta y puja
├── finance/     # depósito, comisión y transacción
└── mail/        # correo del personaje
```

| Módulo | Contenido | Tablas del modelo 2.1 |
|---|---|---|
| `auth` | Cuentas y personajes | `jugador`, `personaje` |
| `inventory` | Catálogo e inventario | `item`, `inventario` |
| `auction` | Subastas y pujas | `subasta`, `puja` |
| `finance` | Movimientos económicos | `deposito`, `comision`, `transaccion` |
| `mail` | Entrega por correo | `correo` |

Las 10 tablas del modelo 2.1 quedan asignadas a un módulo, sin tablas huérfanas
y sin módulos vacíos.

## 2. Relaciones del modelo 2.1

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

Cada bloque del DDL documenta la relación y la cardinalidad de su tabla.

## 3. Archivos por módulo

Los módulos con API (`auth`, `inventory`, `auction`, `mail`) tienen esta forma:

```text
<modulo>/
├── application/
│   ├── dtos.py
│   └── services.py
├── domain/
│   ├── exceptions.py
│   ├── models.py
│   └── repositories.py
├── infrastructure/
│   ├── external_adapters.py
│   ├── models_db.py
│   └── repository_impl.py
└── presentation/
    └── router.py
```

`finance` es un módulo **interno**: no expone endpoints propios, por eso no
tiene `presentation/router.py` ni DTOs. Su servicio (`FinanceService`) se usa
desde `auction` al publicar, cerrar o comprar una subasta.

```text
finance/
├── application/
│   └── services.py
├── domain/
│   ├── exceptions.py
│   ├── models.py
│   └── repositories.py
└── infrastructure/
    ├── external_adapters.py
    ├── models_db.py
    └── repository_impl.py
```

`auth` conserva los cuatro archivos de documentación de la estructura de
referencia:

```text
auth/
├── application/casos_uso-orquestacion.txt
├── domain/reglas_negocio.txt
├── infrastructure/implementacion_tecnica.txt
└── presentation/capa_exposicion.txt
```

### `__init__.py`

- `auth` no tiene `__init__.py`.
- `inventory`, `auction`, `finance` y `mail` tienen `__init__.py` solo en la
  raíz del módulo.
- Las carpetas `application`, `domain`, `infrastructure` y `presentation` no
  llevan `__init__.py`.

## 4. Capas y dependencias

- `domain` no importa FastAPI, SQLAlchemy ni PostgreSQL. Contiene entidades,
  validaciones (`ValueError`) y contratos de repositorio.
- `application` orquesta el dominio y los repositorios; no conoce FastAPI.
- `infrastructure` implementa los repositorios, contiene las entidades ORM y
  los adaptadores externos.
- `presentation` depende de `application` y expone la API REST.
- La comunicación entre módulos se hace por servicios de aplicación:
  `AuthService`, `InventoryService`, `FinanceService` y `MailService`.

## 5. Adaptadores externos

La integración con AzerothCore es de **solo lectura**:

- `auth/infrastructure/external_adapters.py`: cuentas y personajes.
- `inventory/infrastructure/external_adapters.py`: catálogo e inventario.
- `auction`, `finance` y `mail` no consultan WoW en tiempo de ejecución; sus
  adaptadores quedan como puntos de extensión.

El cliente MySQL y el plan de sincronización viven en
`src/integrations/wow/`. Esa carpeta es propia de proyectoX y no existe en
`delivery-monolith`.

## 6. `init.sql` y `main.py`

- `init.sql` está en la **raíz** del proyecto.
- Contiene **solo DDL**: `CREATE TABLE`, PK, FK, `UNIQUE`, `CHECK` e índices.
  No contiene `INSERT`, `UPDATE`, `DELETE` ni `SELECT`.
- Cada tabla tiene un bloque de comentarios con su módulo, su PK, sus FK, su
  cardinalidad y sus reglas.
- Los datos de demostración viven únicamente en `sql/02_seed.sql`.
- `sql/01_schema.sql` es una copia exacta de `init.sql` para ejecuciones
  manuales.
- `src/main.py` importa los `models_db.py` en orden de llaves foráneas:
  `auth`, `inventory`, `auction`, `finance` y `mail`.
- `src/main.py` registra los routers de `auth`, `inventory`, `auction` y
  `mail`. `finance` no se registra porque no tiene endpoints propios.

## 7. Checklist modelo 2.1 → módulo → DDL

| Tabla | Módulo | Comentario en `init.sql` | Estado |
|---|---|---|---|
| `jugador` | `auth` | `auth · JUGADOR` | ✅ |
| `personaje` | `auth` | `auth · PERSONAJE` | ✅ |
| `item` | `inventory` | `inventory · ITEM` | ✅ |
| `inventario` | `inventory` | `inventory · INVENTARIO` | ✅ |
| `subasta` | `auction` | `auction · SUBASTA` | ✅ |
| `puja` | `auction` | `auction · PUJA` | ✅ |
| `deposito` | `finance` | `finance · DEPOSITO` | ✅ |
| `comision` | `finance` | `finance · COMISION` | ✅ |
| `transaccion` | `finance` | `finance · TRANSACCION` | ✅ |
| `correo` | `mail` | `mail · CORREO` | ✅ |

Las columnas `wow_account_id`, `wow_guid` y `wow_entry` son columnas técnicas
de la integración de solo lectura con AzerothCore. No forman parte del modelo
lógico 2.1 y están marcadas como tales en el DDL.
