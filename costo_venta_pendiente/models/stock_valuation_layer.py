from odoo import models, fields, api


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    numero_orden = fields.Char(
        string='Número Orden',
        compute='_compute_orden_info',
        store=True,
        help='Número de orden de venta o compra desde el movimiento de stock relacionado'
    )
    
    cantidad_facturada = fields.Float(
        string='Cantidad Facturada',
        compute='_compute_orden_info',
        store=True,
        help='Cantidad facturada desde la línea de orden de venta'
    )

    @api.depends('stock_move_id', 'stock_move_id.sale_line_id', 'stock_move_id.sale_line_id.order_id', 
                 'stock_move_id.sale_line_id.qty_invoiced', 'stock_move_id.purchase_line_id', 
                 'stock_move_id.purchase_line_id.order_id')
    def _compute_orden_info(self):
        """Computa información de orden de venta y compra desde el movimiento de stock relacionado"""
        for layer in self:
            numero_orden = False
            cantidad_facturada = 0.0
            
            if layer.stock_move_id:
                # Verificar si es una orden de venta
                if layer.stock_move_id.sale_line_id and layer.stock_move_id.sale_line_id.order_id:
                    sale_line = layer.stock_move_id.sale_line_id
                    numero_orden = sale_line.order_id.name
                    cantidad_facturada = sale_line.qty_invoiced
                
                # Verificar si es una orden de compra
                elif layer.stock_move_id.purchase_line_id and layer.stock_move_id.purchase_line_id.order_id:
                    purchase_line = layer.stock_move_id.purchase_line_id
                    numero_orden = purchase_line.order_id.name
            
            layer.numero_orden = numero_orden
            layer.cantidad_facturada = cantidad_facturada 