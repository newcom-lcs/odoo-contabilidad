from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscalyear_lock_date(self):
        res = super()._check_fiscalyear_lock_date()
        for move in self:
            if move.journal_id.type == 'sale':
                lock_date_sales = move.company_id._get_user_sales_lock_date()
                if lock_date_sales and move.date <= lock_date_sales:
                    if self.user_has_groups('account.group_account_manager'):
                        message = _("No se puede agregar/modificar documentos con fecha anterior a la de bloqueo %s.", format_date(self.env, lock_date_sales))
                    else:
                        message = _("No se pueden agregar ni modificar entradas antes de la fecha de cierre del diario de ventas %s, inclusive. Revise la configuración de su empresa o consulte con un asesor.", format_date(self.env, lock_date_sales))
                    raise UserError(message)
        return res