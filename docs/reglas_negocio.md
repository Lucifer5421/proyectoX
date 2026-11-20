# Reglas de negocio — Subastas WoW

## Actores

| Actor | Tipo | Responsabilidad |
|---|---|---|
| Vendedor | Jugador | Publica un ítem, paga depósito, recibe el oro de la venta. |
| Comprador / Postor | Jugador | Puja o compra directa; recibe el ítem por correo. |
| Casa de Subastas / Subastador | Sistema / PNJ | Retiene el ítem, valida fondos, cobra depósito y comisión, controla el tiempo. |
| Sistema de Correo | Sistema | Entrega ítems y oro al ganador o devuelve el ítem al vendedor. |

## Reglas

1. **Propiedad del ítem:** el vendedor debe tener el ítem en su inventario antes de publicar.
2. **Depósito:** al publicar se cobra el **5% del precio de salida**. El depósito no se reembolsa.
3. **Duración:** solo se permiten **2, 8 o 24 horas**.
4. **Precio de salida:** debe ser mayor que 0.
5. **Compra directa:** es opcional; si existe, debe ser mayor que 0.
6. **Puja mínima:** debe superar la puja actual en al menos 0.01. Si no hay pujas, debe superar el precio de salida en al menos 0.01.
7. **Fondos del postor:** el comprador debe tener oro suficiente. El oro de la puja se retiene.
8. **Reembolso:** si un postor es superado, su oro se le devuelve.
9. **Cierre por tiempo:** al vencer, gana la puja más alta.
10. **Comisión:** la casa de subastas cobra el **5% del monto final** de la venta.
11. **Liquidación:** el vendedor recibe `monto final - comisión`; el comprador recibe el ítem por correo.
12. **Expiración sin pujas:** la subasta pasa a `expirada` y el ítem se devuelve al vendedor por correo.
13. **Compra directa:** cierra la subasta de inmediato, reembolsa pujas activas y entrega el ítem por correo.
14. **Ítem retenido:** mientras la subasta está activa, el ítem no está en el inventario del vendedor.
15. **Búsqueda:** `GET /auctions/?q=` filtra por nombre del ítem, sin distinguir mayúsculas.
16. **Filtros de la guía:** se puede filtrar por vendedor (`id_vendedor`), por comprador con puja (`id_comprador`) y por objetos utilizables (`usable=true` junto con `id_personaje`), comparando `personaje.nivel` con `item.nivel_requerido`.
17. **Orden:** `sort` admite `precio_asc`, `precio_desc`, `rareza`, `nivel`, `tiempo` y `vendedor`.
18. **Incremento mínimo:** cada puja debe superar la actual en al menos **0.01** (1 cobre en la convención de este proyecto).
19. **Mayor postor y tiempo restante:** la respuesta de una subasta incluye `id_ganador_actual` y `tiempo_restante` en segundos.
20. **Cancelación:** el vendedor puede cancelar una subasta activa. Se reembolsan las pujas activas y el ítem vuelve a su inventario; el depósito no se devuelve.
21. **Correo con importe:** el correo de una compra o subasta ganada registra el importe pagado en `correo.oro` y en el asunto. Es un dato de la operación: el correo del **comprador** contiene el ítem, no el oro.
22. **Precio de vendedor:** `item.precio_base` es el precio de referencia al que un mercader NPC compraría el objeto; es el dato que el addon de la guía muestra como “precio del vendedor”.

## Estados

### Subasta
- `activa`: recibe pujas y compras directas.
- `vendida`: cerrada con ganador.
- `expirada`: venció sin pujas.
- `cancelada`: cancelada por su vendedor; el ítem volvió a su inventario.

### Puja
- `activa`: es la puja vigente.
- `superada`: otra puja mayor la reemplazó (oro reembolsado).
- `ganadora`: ganó la subasta.

### Correo
- `pendiente`: el ítem/oro aún no fue reclamado.
- `leido`: el jugador abrió el correo.
- `cobrado`: el jugador ya retiró el ítem/oro.
- `devuelto`: el correo se usó para devolver un ítem al vendedor.

## Entidades

| Entidad | Descripción |
|---|---|
| `jugador` | Cuenta del jugador. No guarda oro; el oro vive en el personaje. |
| `personaje` | Personaje del jugador (vendedor o comprador) y su oro. |
| `item` | Ítem subastable. |
| `inventario` | Ítems que posee un personaje. |
| `subasta` | Publicación de un ítem con precio, duración y estado. |
| `puja` | Oferta de un comprador sobre una subasta. |
| `deposito` | Cobro inicial del 5% al publicar. |
| `comision` | Cobro del 5% sobre la venta. |
| `transaccion` | Registro de la operación (puja ganadora o compra directa); el vendedor se deduce de `subasta`. |
| `correo` | Entrega de ítem/oro al ganador o devolución al vendedor. |
