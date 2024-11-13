from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    second_currency_id = fields.Many2one('res.currency', string='Second Currency')

    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        if 'second_currency_id' in vals:
            # Trigger recomputation of second currency fields in all related account.move.line records
            move_lines = self.env['account.move.line'].search([('company_id', '=', self.id)])
            for line in move_lines:
                line._compute_second_currency_values()  # Recompute the fields

            # Update all related account move lines
            move_lines = self.env['account.move.line'].search([('company_id', '=', self.id)])
            for line in move_lines:
                line._compute_balance_second_currency()
        return res