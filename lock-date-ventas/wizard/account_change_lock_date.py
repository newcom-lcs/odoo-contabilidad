from odoo import models, fields

class AccountChangeLockDate(models.TransientModel):
    _inherit = 'account.change.lock.date'

    sales_lock_date = fields.Date(
        string="Fecha de bloqueo para el diario ventas",
        default=lambda self: self.env.company.sales_lock_date,
        help="Los usuarios no podrán modificar documentos de venta con fecha anterior o igual a esta fecha."
    )
    
    def _prepare_lock_date_values(self):
        values = super()._prepare_lock_date_values()
        values['sales_lock_date'] = self.sales_lock_date
        return values
    