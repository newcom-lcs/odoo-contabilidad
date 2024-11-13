from odoo import models, fields, api

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    # Related field to get the second currency from the company
    second_currency_id = fields.Many2one(
        related='company_id.second_currency_id',
        string='Segunda Moneda',
        readonly=True,
        store=True
    )

    # Computed fields for summed values from account.analytic.line
    debit_second_currency = fields.Monetary(
        string='Debe (USD)',
        currency_field='second_currency_id',
        compute='_compute_second_currency_totals',
        store=True
    )
    
    credit_second_currency = fields.Monetary(
        string='Haber (USD)',
        currency_field='second_currency_id',
        compute='_compute_second_currency_totals',
        store=True
    )

    amount_second_currency = fields.Monetary(
        string='Saldo (USD)',
        currency_field='second_currency_id',
        compute='_compute_second_currency_totals',
        store=True
    )

    @api.depends('line_ids.debit_second_currency', 'line_ids.credit_second_currency', 'line_ids.amount_second_currency')
    def _compute_second_currency_totals(self):
        for account in self:
            total_debit = sum(line.debit_second_currency for line in account.line_ids)
            total_credit = sum(line.credit_second_currency for line in account.line_ids)
            total_amount = sum(line.amount_second_currency for line in account.line_ids)
            account.debit_second_currency = total_debit
            account.credit_second_currency = total_credit
            account.amount_second_currency = total_amount
