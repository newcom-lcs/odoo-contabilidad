from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    sales_lock_date = fields.Date(
        string="Fecha de bloqueo para el diario ventas",
        tracking=True,
        help="Los usuarios no podrán modificar documentos de venta con fecha anterior o igual a esta fecha."
    )

    def _get_user_sales_lock_date(self):
        """Devuelve la fecha de bloqueo de ventas para esta compañía."""
        self.ensure_one()
        return self.sales_lock_date