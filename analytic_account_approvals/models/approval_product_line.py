from odoo import api, fields, models

class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        help="Analytic account to which this line will be distributed",
    )
    analytic_distribution = fields.Json(string="Cuenta Analítica")
    analytic_precision = fields.Integer(
        string="Analytic Precision",
        default=lambda self: self.env['decimal.precision'].precision_get('Percentage'),
    )

    # Pass analytic account to purchase order line when creating PO
    def _prepare_purchase_order_line(self, purchase_order):
        result = super(ApprovalProductLine, self)._prepare_purchase_order_line(purchase_order)
        
        # For Odoo 16, purchase order lines use 'analytic_distribution' for both single and multiple accounts
        if self.analytic_account_id:
            # If using a single analytic account, convert it to distribution format
            result['analytic_distribution'] = {str(self.analytic_account_id.id): 100}
        elif self.analytic_distribution:
            # If using analytic distribution, just pass it directly
            result['analytic_distribution'] = self.analytic_distribution
            
        return result 