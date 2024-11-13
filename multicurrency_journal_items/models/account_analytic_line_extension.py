from odoo import models, fields, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # Create a related field to the move line, assuming there is a relation
    move_line_id = fields.Many2one('account.move.line', string='Journal Item')

    # Use related fields to fetch values from the account_move_line model
    second_currency_id = fields.Many2one(
        related='move_line_id.second_currency_id',
        store=True,
        readonly=True,
        string='Segunda Moneda'
    )

    currency_rate_second_currency = fields.Float(
        related='move_line_id.currency_rate_second_currency',
        store=True,
        readonly=True,
        string='Tasa de Cambio (USD)'
    )

    debit_second_currency = fields.Monetary(
        related='move_line_id.debit_second_currency',
        currency_field='second_currency_id',
        store=True,
        readonly=True,
        string='Debito (USD)'
    )

    credit_second_currency = fields.Monetary(
        related='move_line_id.credit_second_currency',
        currency_field='second_currency_id',
        store=True,
        readonly=True,
        string='Credito (USD)'
    )


    balance_second_currency = fields.Monetary(
        related='move_line_id.balance_second_currency',
        currency_field='second_currency_id',
        store=True,
        readonly=True,
        string='Balance (USD)'
    )

    amount_second_currency = fields.Monetary(
        string='Amount in Second Currency',
        currency_field='second_currency_id',
        related='move_line_id.amount_second_currency',
        store=True,
        readonly=True
    )