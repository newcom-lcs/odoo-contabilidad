from odoo import models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def post(self):
        # Itera sobre cada asiento que se intenta publicar.
        for move in self:
            lock_date = move.company_id._get_user_sales_lock_date()

            if not lock_date:
                continue

            if move.journal_id.type == 'sale' and move.date <= lock_date:
                raise UserError(
                    _("No puedes publicar asientos de venta en o antes de la fecha de bloqueo (%s) porque el diario de ventas está cerrado.", lock_date)
                )

        return super(AccountMove, self).post()


    # def _check_fiscalyear_lock_date(self):
    #     res = super()._check_fiscalyear_lock_date()
    #     for move in self:
    #         if move.journal_id == 'Facturas de Clientes':
    #             lock_date_sales = move.company_id._get_user_sales_lock_date()
    #             if lock_date_sales and move.date <= lock_date_sales:
    #                 if self.user_has_groups('account.group_account_manager'):
    #                     message = _("You cannot add/modify entries prior to and inclusive of the lock date %s.", format_date(self.env, lock_date_sales))
    #                 else:
    #                     message = _("Entries cannot be added or modified before the sales journal lock date %s, inclusive. Please check your company settings or consult an advisor.", format_date(self.env, lock_date_sales))
    #                 raise UserError(message)
    #     return res