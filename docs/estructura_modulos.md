# Estructura modular de proyectoX

Este documento adapta la estructura del monolito modular de referencia
(`delivery-monolith`) y las indicaciones de la transcripción del audio al
dominio de **subastas de World of Warcraft**.

`delivery-monolith` se usa **solo como molde arquitectónico**: no se copian
sus módulos, tablas ni reglas de negocio.

## 1. Mapeo de módulos

| Módulo de referencia | Módulo en proyectoX | Entidades / tablas |
|---|---|---|
| `auth` | `auth` | `jugador`, `personaje` |
| `restaurant` | `inventory` | `item`, `inventario` |
| `order` / `tracking` | `auction` | `subasta`, `puja` |
| `payment` | `finance` | `deposito`, `comision`, `transaccion`, `correo` |

> **No existe un módulo `restaurant/` en proyectoX.** Ese nombre pertenece
> al dominio de delivery. En este proyecto el catálogo de productos se
> representa con `inventory/` (ítems e inventario de personajes), que es el
> módulo que ocupa su lugar en la arquitectura.

## 2. Capas obligatorias por módulo

Cada módulo de `src/modules/<modulo>/` contiene exactamente estas capas:

```
<modulo>/
├── domain/
│   ├── exceptions.py       # excepciones propias del dominio
│   ├── models.py           # entidades y reglas de negocio puras
│   └── repositories.py     # interfaces/abstracciones de persistencia
├── application/
│   ├── datos.py            # contratos de datos (DTO) del módulo
│   └── services.py         # casos de uso y orquestación
├── infrastructure/
│   ├── external_adapter.py # integración con servicios externos
│   ├── models_db.py        # modelos ORM de SQLAlchemy
│   └── repositories_impl.py# implementación concreta de repositorios
└── presentation/
    ├── routers.py          # endpoints FastAPI
    └── schemas.py          # esquemas Pydantic expuestos por la API
```

### Reglas de dependencia

- `domain` no importa FastAPI, SQLAlchemy ni otros módulos.
- `application` usa el dominio y las interfaces de repositorio; no conoce
  FastAPI.
- `infrastructure` implementa las interfaces y contiene el ORM/adaptadores.
- `presentation` depende de `application` y expone la API.
- La comunicación entre módulos se hace por los servicios de aplicación
  (`AuthService`, `InventoryService`, `FinanceService`), no por SQL directo.

## 3. Adaptadores externos

La integración con AzerothCore es de **solo lectura**:

- `auth/infrastructure/external_adapter.py`: cuentas y personajes.
- `inventory/infrastructure/external_adapter.py`: catálogo e inventario.
- `auction` y `finance` no consultan WoW en tiempo de ejecución; sus
  adaptadores quedan como puntos de extensión.

El cliente MySQL y el plan de sincronización viven en
`src/integrations/wow/` para no mezclar la lógica de terceros con las reglas
de negocio.

## 4. init.sql y main.py

- `init.sql` está en la **raíz** del proyecto, no dentro de `src/core/`.
- Sus tablas están separadas con comentarios por módulo:
  `auth`, `inventory`, `auction` y `finance`.
- `src/main.py` importa los `models_db.py` de todos los módulos antes de
  `Base.metadata.create_all` y registra todos los `routers.py` con
  `app.include_router(...)`.
