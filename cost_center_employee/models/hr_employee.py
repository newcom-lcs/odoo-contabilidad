# my_custom_module/models/hr_employee.py
from odoo import models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    default_analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Centro de Costos'
    )
    allowed_journal_ids = fields.Many2many(
        'account.journal',
        string='Metodo de Pago (Default)',
        domain=[('type', 'in', ['bank', 'cash'])]
    )
