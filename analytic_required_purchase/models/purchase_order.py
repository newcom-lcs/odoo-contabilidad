from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    requires_analytic = fields.Boolean(
        compute='_compute_requires_analytic',
        store=True
    )

    @api.depends('product_id')
    def _compute_requires_analytic(self):
        for line in self:
            line.requires_analytic = bool(
                line.product_id and 
                line.product_id.property_account_expense_id and
                line.product_id.property_account_expense_id.analytic_distribution_required
            )

    @api.constrains('analytic_distribution')
    def _check_analytic_required(self):
        for line in self:
            if line.requires_analytic and not line.analytic_distribution:
                raise ValidationError(_("La cuenta analítica es requerida."))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    requires_analytic = fields.Boolean(
        compute='_compute_requires_analytic',
        store=True
    )

    @api.depends('product_id', 'account_id')
    def _compute_requires_analytic(self):
        for line in self:
            line.requires_analytic = bool(
                line.product_id and 
                line.account_id and
                line.account_id.analytic_distribution_required
            )

    @api.constrains('analytic_distribution')
    def _check_analytic_required(self):
        for line in self:
            if line.requires_analytic and not line.analytic_distribution:
                raise ValidationError(_("La cuenta analítica es requerida.")) 