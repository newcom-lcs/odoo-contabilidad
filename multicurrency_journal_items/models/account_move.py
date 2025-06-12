from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_untaxed_signed_second_currency = fields.Monetary(
        string='Untaxed Amount Signed (USD)',
        currency_field='second_currency_id',
        compute='_compute_amount_untaxed_signed_second_currency',
        store=True
    )
    amount_total_second_currency = fields.Monetary(
        string='Total Amount (USD)',
        currency_field='second_currency_id',
        compute='_compute_amount_total_second_currency',
        store=True
    )
    amount_tax_second_currency = fields.Monetary(
        string='Tax Amount (USD)',
        currency_field='second_currency_id',
        compute='_compute_amount_tax_second_currency',
        store=True
    )
    amount_residual_signed_second_currency = fields.Monetary(
        string='Residual Amount Signed (USD)',
        currency_field='second_currency_id',
        compute='_compute_amount_residual_signed_second_currency',
        store=True
    )
    second_currency_id = fields.Many2one(
        related='company_id.second_currency_id',
        store=True,
        readonly=True,
        string='Second Currency'
    )

    @api.depends('amount_untaxed_signed', 'company_id', 'date', 'second_currency_id')
    def _compute_amount_untaxed_signed_second_currency(self):
        for move in self:
            if move.second_currency_id:
                move.amount_untaxed_signed_second_currency = move.company_currency_id._convert(
                    move.amount_untaxed_signed,
                    move.second_currency_id,
                    move.company_id,
                    move.date,
                )
            else:
                move.amount_untaxed_signed_second_currency = 0.0

    @api.depends('amount_total_signed', 'company_id', 'date', 'second_currency_id')
    def _compute_amount_total_second_currency(self):
        for move in self:
            if move.second_currency_id:
                move.amount_total_second_currency = move.company_currency_id._convert(
                    move.amount_total_signed,
                    move.second_currency_id,
                    move.company_id,
                    move.date,
                )
            else:
                move.amount_total_second_currency = 0.0

    @api.depends('amount_tax_signed', 'company_id', 'date', 'second_currency_id')
    def _compute_amount_tax_second_currency(self):
        for move in self:
            if move.second_currency_id:
                move.amount_tax_second_currency = move.company_currency_id._convert(
                    move.amount_tax_signed,
                    move.second_currency_id,
                    move.company_id,
                    move.date,
                )
            else:
                move.amount_tax_second_currency = 0.0

    @api.depends('amount_residual_signed', 'company_id', 'date', 'second_currency_id', 'line_ids.matched_debit_ids', 'line_ids.matched_credit_ids')
    def _compute_amount_residual_signed_second_currency(self):
        for move in self:
            if move.second_currency_id:
                move.amount_residual_signed_second_currency = move.company_currency_id._convert(
                    move.amount_residual_signed,
                    move.second_currency_id,
                    move.company_id,
                    move.date,
                )
            else:
                move.amount_residual_signed_second_currency = 0.0 