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
6. **Puja mínima:** debe superar la puja actual. Si no hay pujas, debe superar el precio de salida.
7. **Fondos del postor:** el comprador debe tener oro suficiente. El oro de la puja se retiene.
8. **Reembolso:** si un postor es superado, su oro se le devuelve.
9. **Cierre por tiempo:** al vencer, gana la puja más alta.
10. **Comisión:** la casa de subastas cobra el **5% del monto final** de la venta.
11. **Liquidación:** el vendedor recibe `monto final - comisión`; el comprador recibe el ítem por correo.
12. **Expiración sin pujas:** la subasta pasa a `expirada` y el ítem se devuelve al vendedor por correo.
13. **Compra directa:** cierra la subasta de inmediato, reembolsa pujas activas y entrega el ítem por correo.
14. **Ítem retenido:** mientras la subasta está activa, el ítem no está en el inventario del vendedor.

## Estados

### Subasta
- `activa`: recibe pujas y compras directas.
- `vendida`: cerrada con ganador.
- `expirada`: venció sin pujas.
- `cancelada`: reservada para una futura cancelación administrativa.

### Puja
- `activa`: es la puja vigente.
- `superada`: otra puja mayor la reemplazó (oro reembolsado).
- `ganadora`: ganó la subasta.

### Correo
- `pendiente`: el ítem/oro aún no fue reclamado.
- `entregado`: el jugador ya lo reclamó.

## Entidades

| Entidad | Descripción |
|---|---|
| `jugador` | Cuenta del jugador. |
| `personaje` | Personaje del jugador (vendedor o comprador). |
| `item` | Ítem subastable. |
| `inventario` | Ítems que posee un personaje. |
| `subasta` | Publicación de un ítem con precio, duración y estado. |
| `puja` | Oferta de un comprador sobre una subasta. |
| `deposito` | Cobro inicial del 5% al publicar. |
| `comision` | Cobro del 5% sobre la venta. |
| `transaccion` | Registro de la operación (puja o compra directa). |
| `correo` | Entrega de ítem/oro al ganador o devolución al vendedor. |
