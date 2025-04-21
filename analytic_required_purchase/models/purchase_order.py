from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    requires_analytic = fields.Boolean(
        compute='_compute_requires_analytic',
        store=True,
        help="Technical field to determine if analytic account is required"
    )

    @api.depends('product_id')
    def _compute_requires_analytic(self):
        for line in self:
            line.requires_analytic = bool(
                line.product_id and 
                line.product_id.detailed_type == 'service' and 
                line.product_id.property_account_expense_id
            )

    @api.constrains('product_id', 'analytic_distribution')
    def _check_analytic_required(self):
        for line in self:
            if line.requires_analytic and not line.analytic_distribution:
                raise ValidationError(_(
                    "La cuenta analítica es requerida para productos de servicio con cuenta de gastos."
                )) 