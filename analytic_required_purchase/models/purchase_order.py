from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    requires_analytic = fields.Boolean(
        compute='_compute_requires_analytic',
        store=True
    )

    analytic_distribution = fields.Json(
        string="Analytic",
        compute="_compute_analytic_distribution",
        store=True,
        readonly=False,
        states={
            'done': [('readonly', True)], 
            'cancel': [('readonly', True)],
            'draft': [('readonly', lambda self: not self.requires_analytic)],
            'sent': [('readonly', lambda self: not self.requires_analytic)],
            'to approve': [('readonly', lambda self: not self.requires_analytic)],
            'purchase': [('readonly', lambda self: not self.requires_analytic)],
        },
        help="Analytic distribution for this line"
    )

    @api.depends('product_id')
    def _compute_requires_analytic(self):
        for line in self:
            was_required = line.requires_analytic
            line.requires_analytic = bool(
                line.product_id and 
                line.product_id.property_account_expense_id and
                line.product_id.property_account_expense_id.analytic_distribution_required
            )
            # Clear analytic distribution if it's no longer required
            if was_required and not line.requires_analytic:
                line.analytic_distribution = False

    @api.depends('requires_analytic')
    def _compute_analytic_distribution(self):
        for line in self:
            if not line.requires_analytic:
                line.analytic_distribution = False

    @api.constrains('analytic_distribution')
    def _check_analytic_required(self):
        for line in self:
            if line.requires_analytic and not line.analytic_distribution:
                raise ValidationError(_("La cuenta analítica es requerida.")) 