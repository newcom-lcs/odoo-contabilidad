from odoo import models, fields, api

class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    allowed_journal_ids = fields.Many2many(
        'account.journal',
        string='Metodo de Pago (Default)',
        related='employee_id.allowed_journal_ids',
        readonly=True
    )

    @api.model
    def default_get(self, fields):
        defaults = super(HRExpenseSheet, self).default_get(fields)
        if 'employee_id' in defaults:
            employee = self.env['hr.employee'].browse(defaults['employee_id'])
            if employee.allowed_journal_ids:
                defaults['bank_journal_id'] = employee.allowed_journal_ids[0].id
        return defaults

class HRExpense(models.Model):
    _inherit = 'hr.expense'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'employee_id' in vals:
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                if employee.default_analytic_account_id and not vals.get('analytic_distribution'):
                    vals['analytic_distribution'] = {employee.default_analytic_account_id.id: 100}
        return super(HRExpense, self).create(vals_list)
