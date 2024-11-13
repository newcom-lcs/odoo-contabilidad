from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    currency_rate_second_currency = fields.Float(
        string='Tasa de Cambio',
        compute='_compute_second_currency_values',
        store=True
    )
    debit_second_currency = fields.Monetary(
        string='Debito (USD)',
        currency_field='second_currency_id',
        compute='_compute_second_currency_values',
        store=True
    )
    credit_second_currency = fields.Monetary(
        string='Credito (USD)',
        currency_field='second_currency_id',
        compute='_compute_second_currency_values',
        store=True
    )
    second_currency_id = fields.Many2one(
        related='company_id.second_currency_id',
        store=True,
        readonly=True,
        string='Segunda Moneda'
    )
    balance_second_currency = fields.Monetary(
        string="Balance (USD)",
        currency_field='second_currency_id',
        compute='_compute_balance_second_currency',
        store=True
    )
    amount_second_currency = fields.Monetary(
        string='Amount (USD)',
        currency_field='second_currency_id',
        compute='_compute_amount_second_currency',
        store=True
    )

    @api.depends('debit', 'credit', 'company_id', 'date', 'second_currency_id')
    def _compute_second_currency_values(self):
        for line in self:
            if line.second_currency_id:
                # Get the conversion rate
                currency_rate = line.company_currency_id._get_conversion_rate(
                    line.company_currency_id,
                    line.second_currency_id,
                    line.company_id,
                    line.date,
                )
                line.currency_rate_second_currency = currency_rate

                currency_rate = line.second_currency_id._convert(
                    1.0, 
                    line.company_currency_id, 
                    line.company_id, 
                    line.date
                )
                line.currency_rate_second_currency = currency_rate
                
                # Convert debit amount
                line.debit_second_currency = line.company_currency_id._convert(
                    line.debit,
                    line.second_currency_id,
                    line.company_id,
                    line.date,
                ) if line.debit else 0.0

                # Convert credit amount
                line.credit_second_currency = line.company_currency_id._convert(
                    line.credit,
                    line.second_currency_id,
                    line.company_id,
                    line.date,
                ) if line.credit else 0.0
            else:
                line.currency_rate_second_currency = 0.0
                line.debit_second_currency = 0.0
                line.credit_second_currency = 0.0

    @api.depends('debit_second_currency', 'credit_second_currency')
    def _compute_amount_second_currency(self):
        for line in self:
            line.amount_second_currency = line.credit_second_currency - line.debit_second_currency

    @api.depends('debit_second_currency', 'credit_second_currency')
    def _compute_balance_second_currency(self):
        for line in self:
            line.balance_second_currency = line.debit_second_currency - line.credit_second_currency
