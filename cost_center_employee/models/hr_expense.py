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
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'employee_id' in defaults:
            employee = self.env['hr.employee'].browse(defaults['employee_id'])
            if employee.allowed_journal_ids:
                defaults['bank_journal_id'] = employee.allowed_journal_ids[0].id
        return defaults

    @api.onchange('employee_id')
    def _onchange_employee_id_journal(self):
        if self.employee_id.allowed_journal_ids:
            self.bank_journal_id = self.employee_id.allowed_journal_ids[0]


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'employee_id' in vals:
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                if employee.default_analytic_account_id and not vals.get('analytic_distribution'):
                    vals['analytic_distribution'] = {employee.default_analytic_account_id.id: 100}
        return super().create(vals_list)

    @api.onchange('employee_id')
    def _onchange_employee_id_analytic(self):
        if self.employee_id.default_analytic_account_id:
            self.analytic_distribution = {self.employee_id.default_analytic_account_id.id: 100}
