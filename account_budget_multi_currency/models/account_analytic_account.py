from odoo import models, fields, api

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    # Define the One2many relationship to crossovered.budget.lines
    crossovered_budget_line_ids = fields.One2many(
        'crossovered.budget.lines', 'analytic_account_id', string='Lineas de Presupuesto'
    )

    # Define the computed field
    total_custom_planned_amount = fields.Float(
        string="Total Custom Planned Amount", 
        compute='_compute_total_custom_planned_amount',
        store=True
    )

    # Field to store the gross margin in the second currency
    gross_margin_second_currency = fields.Monetary(
        string="Gross Margin (Second Currency)",
        compute='_compute_gross_margin_second_currency',
        currency_field='second_currency_id',  # Ensure this currency field exists
        store=True
    )

    @api.depends('crossovered_budget_line_ids.custom_planned_amount')
    def _compute_total_custom_planned_amount(self):
        for account in self:
            total = sum(account.crossovered_budget_line_ids.mapped('custom_planned_amount'))
            account.total_custom_planned_amount = total

    def action_show_custom_planned_amount(self):
        """
        This method should be triggered by the smart button
        For now, it will open a view of related budget lines.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Custom Planned Amount Lines',
            'view_mode': 'tree,form',
            'res_model': 'crossovered.budget.lines',
            'domain': [('analytic_account_id', '=', self.id)],
            'context': dict(self.env.context),
        }

    @api.depends('line_ids.amount_second_currency')
    def _compute_gross_margin_second_currency(self):
        """
        Compute the sum of amount_second_currency from related account.analytic.line records
        """
        for account in self:
            # Summing the amount_second_currency field of all analytic lines related to this account
            total_second_currency = sum(account.line_ids.mapped('amount_second_currency'))
            account.gross_margin_second_currency = total_second_currency

        
    def action_show_gross_margin_second_currency(self):
        """
        This method is called when the 'Gross Margin (Second Currency)' button is clicked.
        For now, it can show a list view of related analytic lines or perform another action.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Analytic Lines',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'domain': [('account_id', '=', self.id)],  # Filter for lines related to this analytic account
            'context': {'default_account_id': self.id},
        }