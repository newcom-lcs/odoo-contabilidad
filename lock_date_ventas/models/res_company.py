from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    sales_lock_date = fields.Date(
        string="Fecha de bloqueo para el diario ventas",
        default=lambda self: self.env.company.sales_lock_date,
        help="Los usuarios no podrán modificar documentos de venta con fecha anterior o igual a esta fecha."
    )

    def _get_user_sales_lock_date(self):
        return self.sales_lock_date