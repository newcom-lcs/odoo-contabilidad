from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    so_tipo_negocio = fields.Char(
        string='Tipo de Negocio',
        compute='_compute_so_related_fields',
        store=True,
        search='_search_so_tipo_negocio',
        groups='account.group_account_invoice'
    )
    so_business_unit_id = fields.Many2one(
        'business.unit',
        string='Business Unit',
        compute='_compute_so_related_fields',
        store=True,
        search='_search_so_business_unit_id',
        groups='account.group_account_invoice'
    )
    so_margen_teorico_display = fields.Char(
        string='Margen Teórico',
        compute='_compute_so_related_fields',
        store=True,
        search='_search_so_margen_teorico_display',
        groups='account.group_account_invoice'
    )

    @api.depends('invoice_origin')
    def _compute_so_related_fields(self):
        SaleOrder = self.env['sale.order']
        for move in self:
            move.so_tipo_negocio = False
            move.so_business_unit_id = False
            move.so_margen_teorico_display = False
            if move.invoice_origin:
                so = SaleOrder.search([('name', '=', move.invoice_origin)], limit=1)
                if so:
                    tipo_negocio = getattr(so, 'tipo_negocio', False)
                    move.so_tipo_negocio = str(tipo_negocio).upper() if tipo_negocio else False
                    move.so_business_unit_id = getattr(so, 'business_unit_id', False)
                    move.so_margen_teorico_display = getattr(so, 'margen_teorico_display', False)

    def _search_so_tipo_negocio(self, operator, value):
        SaleOrder = self.env['sale.order']
        sos = SaleOrder.search([('tipo_negocio', operator, value)])
        if sos:
            return [('invoice_origin', 'in', sos.mapped('name'))]
        return [('id', '=', False)]

    def _search_so_business_unit_id(self, operator, value):
        SaleOrder = self.env['sale.order']
        sos = SaleOrder.search([('business_unit_id', operator, value)])
        if sos:
            return [('invoice_origin', 'in', sos.mapped('name'))]
        return [('id', '=', False)]

    def _search_so_margen_teorico_display(self, operator, value):
        SaleOrder = self.env['sale.order']
        sos = SaleOrder.search([('margen_teorico_display', operator, value)])
        if sos:
            return [('invoice_origin', 'in', sos.mapped('name'))]
        return [('id', '=', False)] 