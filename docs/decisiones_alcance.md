# Decisiones de alcance del proyecto

Este documento responde las 4 preguntas de alcance usando como base los materiales
del curso (`delivery-monolith`, transcripción, PDF de actores y documento de WoW Classic).
`delivery-monolith` se usa **solo como guía estructural**; no se modifica.

---

## 1. ¿PostgreSQL aparte o MySQL integrado al WoW?

**Recomendado: PostgreSQL aparte.**

| Criterio | PostgreSQL aparte | MySQL integrado |
|---|---|---|
| Coincide con el molde | Sí (el molde usa PostgreSQL) | No |
| Riesgo para el servidor WoW | Ninguno | Alto (se toca la BD del juego) |
| Facilidad de demostración | Alta (contenedor aislado) | Media (depende del mundo) |
| SQLAlchemy / DDD | Directo | Requiere adaptar el driver |
| Datos reales del juego | No | Sí |

**Por qué:** la entrega de la clase de base de datos evalúa modelo ER, SQL, DDD y API.
El molde `delivery-monolith` ya trae PostgreSQL, `psycopg2` y SQLAlchemy; seguirlo
reduce el riesgo y permite demostrar el módulo sin tocar el MySQL de AzerothCore.
El MySQL del servidor se queda para el juego. Si más adelante se pide integración real,
solo se cambia `DATABASE_URL` y se adapta el repositorio.

---

## 2. ¿El grupo hace solo subastas o varios módulos?

**Recomendado: cinco módulos propios del dominio de subastas**:
`auth` (`jugador`, `personaje`), `inventory` (`item`, `inventario`),
`auction` (`subasta`, `puja`), `finance` (`deposito`, `comision`,
`transaccion`) y `mail` (`correo`).

**Por qué:** la subasta necesita cuentas, personajes, ítems, inventario,
registros financieros y entrega por correo. Los nombres salen del modelo
lógico 2.1 y no de `delivery-monolith`. `inventory` contiene el catálogo de
ítems, `auction` las subastas y pujas, `finance` los movimientos económicos y
`mail` la entrega al ganador o la devolución al vendedor. No hay módulos
vacíos. El detalle del mapeo y de las capas está en
[`estructura_modulos.md`](estructura_modulos.md).

---

## 3. ¿Solo la BD, la API o todo?

**Recomendado: todo (BD + API + presentación + documentación).**

- **BD:** modelo conceptual, modelo lógico, `init.sql` (DDL puro) y
  `sql/02_seed.sql` (datos de demostración).
- **Aplicación:** dominio, casos de uso y repositorios.
- **Presentación:** API FastAPI con endpoints de subastas, pujas, compra directa,
  cierre, cuentas/personajes, inventario y correo.
- **Documentación:** reglas de negocio, decisiones y diagramas.

**Por qué:** el molde tiene las 4 capas y la transcripción pide organizar el código y
completar módulos. Entregar solo la BD dejaría fuera la parte de DDD y la API, que es
justamente lo que diferencia este trabajo de un simple script SQL.

---

## 4. ¿`mod-auctionsim` entra en la entrega o es opcional?

**Recomendado: opcional / no entra en la entrega principal.**

**Por qué:** `mod-auctionsim` es un módulo C++ de AzerothCore que requiere recompilar
el `worldserver`. El PDF de la tarea pide identificar actores, entidades y modelos; el
molde es Python/FastAPI/PostgreSQL. La entrega académica se cubre con la BD + API.
Si el profesor pide la funcionalidad dentro del juego, se instala como extra y se
documenta aparte; no debe ser un requisito para aprobar el módulo de base de datos.

---

## Resumen

| Pregunta | Decisión |
|---|---|
| Motor | PostgreSQL aparte (contenedor propio) |
| Alcance | Cinco módulos propios del modelo 2.1: auth, inventory, auction, finance y mail |
| Entregable | BD + API + presentación + documentación |
| `mod-auctionsim` | Opcional, fuera de la entrega principal |
