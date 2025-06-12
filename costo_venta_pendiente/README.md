# Módulo de Capa de Valoración de Stock - Información de Órdenes

Este módulo de Odoo extiende la capa de valoración de stock para incluir información de órdenes de venta y compra.

## Características

- Agrega campo **Número Orden** (unificado para venta y compra) a la capa de valoración de stock
- Agrega campo **Cantidad Facturada** desde la línea de orden de venta
- Los campos se muestran en la vista de árbol de la capa de valoración después de la columna fecha de creación
- **Filtro predefinido "Sin Facturar"** para identificar registros con cantidad_facturada = 0

## Instalación

1. Copia este módulo a tu directorio de addons de Odoo
2. Actualiza la lista de addons en Odoo
3. Instala el módulo "Stock Valuation Layer - Información de Órdenes"

## Dependencias

- `stock_account` - Para funcionalidad de capa de valoración de stock
- `sale_stock` - Para integración de órdenes de venta y movimientos de stock
- `purchase_stock` - Para integración de órdenes de compra y movimientos de stock

## Detalles Técnicos

### Campos Agregados

- `numero_orden`: Campo Char que contiene el número de orden (venta o compra)
- `cantidad_facturada`: Campo Float que contiene la cantidad facturada desde la línea de orden de venta

### Lógica de Cálculo

Los campos se calculan de la siguiente manera:
1. Toma el `stock_move_id` de la capa de valoración
2. Verifica si el movimiento está relacionado con una orden de venta (`sale_line_id`)
3. Si es orden de venta: extrae el número de orden de `sale_line.order_id.name` y obtiene la cantidad facturada de `sale_line.qty_invoiced`
4. Si es orden de compra: extrae el número de orden de `purchase_line.order_id.name`

### Extensión de Vista

El módulo extiende la vista `stock_account.stock_valuation_layer_tree` para agregar los nuevos campos después de la columna `create_date`.

### Filtros Agregados

- **"Sin Facturar"**: Filtro predefinido que muestra todos los registros donde `cantidad_facturada = 0`

## Uso

Después de la instalación, puedes:
1. Ir a Inventario > Reportes > Valoración de Stock
2. Las nuevas columnas "Número Orden" y "Cantidad Facturada" aparecerán después de la columna "Fecha de Creación"
3. Estos campos se poblarán automáticamente para las capas de valoración relacionadas con órdenes de venta o compra
4. **Usar el filtro "Sin Facturar"** para identificar rápidamente todos los registros que no han sido facturados

## Notas

- Los campos se almacenan (calculados y almacenados) para mejor rendimiento
- Los campos son opcionales en la vista (se pueden mostrar/ocultar según sea necesario)
- Solo las capas de valoración relacionadas con movimientos de stock de órdenes de venta o compra tendrán estos campos poblados
- El campo "Número Orden" muestra el número de la orden independientemente de si es venta o compra
- Para órdenes de venta, se mostrará también la cantidad facturada
- Para órdenes de compra, solo se mostrará el número de orden
- El filtro "Sin Facturar" es muy útil para identificar movimientos pendientes de facturación 