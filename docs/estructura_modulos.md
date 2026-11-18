# Estructura modular de proyectoX

Este documento fija la estructura de `proyectoX` tomando como molde exacto
`delivery-monolith`. La diferencia es el dominio: donde delivery habla de
restaurantes, repartidores y pagos, proyectoX habla de ítems, subastas, pujas
y finanzas de World of Warcraft.

`delivery-monolith` **no se modifica**. Solo se copia su organización de
carpetas, archivos y capas.

## 1. Módulos

La estructura de módulos es la misma de delivery:

```text
src/modules/
├── auth/
├── order/
├── payment/
├── restaurant/
└── tracking/
```

| Módulo | Contenido en proyectoX | Tablas |
|---|---|---|
| `auth` | Jugadores y personajes | `jugador`, `personaje` |
| `restaurant` | Catálogo de ítems e inventario | `item`, `inventario` |
| `order` | Subastas y pujas | `subasta`, `puja` |
| `payment` | Depósitos, comisiones, transacciones y correo | `deposito`, `comision`, `transaccion`, `correo` |
| `tracking` | Sin equivalente en proyectoX | — |

El nombre `restaurant` se conserva por exigencia de la estructura de delivery,
aunque su contenido sea el catálogo de ítems (`Item`) y el inventario
(`Inventario`) de proyectoX. Lo mismo ocurre con `order` (subastas) y
`payment` (finanzas).

## 2. Archivos por módulo

Cada módulo tiene exactamente esta forma:

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

Además, `auth` incluye los cuatro archivos de documentación que trae delivery:

```text
auth/
├── application/casos_uso-orquestacion.txt
├── domain/reglas_negocio.txt
├── infrastructure/implementacion_tecnica.txt
└── presentation/capa_exposicion.txt
```

`order` conserva en la raíz los archivos `models.py` y `services.py` que
existen en delivery.

### Archivos que se dejan en blanco

Se dejan vacíos los archivos de delivery que **no tienen contenido propio en
proyectoX**, para no inventar código ni duplicar responsabilidades:

| Archivo | Por qué queda en blanco |
|---|---|
| `tracking/**` | proyectoX no tiene repartidores, rutas ni ubicación en tiempo real. El seguimiento de una subasta (pujas, cierre y expiración) vive en `order`. |
| `order/models.py` | En proyectoX los modelos de subasta están en `order/domain/models.py`. |
| `order/services.py` | En proyectoX los casos de uso están en `order/application/services.py`. |

El resto de archivos sí contiene el código real de proyectoX: entidades,
DTO, servicios, repositorios, modelos ORM, adaptadores y routers.

### `__init__.py`

Se replica la regla de delivery:

- `auth` **no** tiene `__init__.py`.
- `order`, `payment`, `restaurant` y `tracking` tienen `__init__.py` solo en
  la raíz del módulo.
- Las carpetas `application`, `domain`, `infrastructure` y `presentation` no
  llevan `__init__.py`.

## 3. Capas y dependencias

- `domain` no importa FastAPI, SQLAlchemy ni otros módulos.
- `application` usa el dominio y las interfaces de repositorio; no conoce
  FastAPI.
- `infrastructure` implementa las interfaces, contiene el ORM y los
  adaptadores externos.
- `presentation` depende de `application` y expone la API.
- La comunicación entre módulos se hace por los servicios de aplicación
  (`AuthService`, `InventoryService`, `FinanceService`), no por SQL directo.

## 4. Adaptadores externos

La integración con AzerothCore es de **solo lectura**:

- `auth/infrastructure/external_adapters.py`: cuentas y personajes.
- `restaurant/infrastructure/external_adapters.py`: catálogo e inventario.
- `order` y `payment` no consultan WoW en tiempo de ejecución; sus
  adaptadores quedan como puntos de extensión.

El cliente MySQL y el plan de sincronización viven en
`src/integrations/wow/`. Esa carpeta es propia de proyectoX y no existe en
delivery; se mantiene separada para no mezclar la lógica de terceros con las
reglas de negocio.

## 5. `init.sql` y `main.py`

- `init.sql` está en la **raíz** del proyecto, no dentro de `src/core/`.
- Sus tablas están separadas con comentarios por módulo:
  `auth`, `restaurant`, `order` y `payment`.
- `src/main.py` importa los `models_db.py` en el orden de delivery:
  `auth`, `restaurant`, `tracking`, `order` y `payment`.
- `src/main.py` registra los routers de `auth`, `restaurant`, `order` y
  `payment`. `tracking` no se registra porque no tiene endpoints propios.
