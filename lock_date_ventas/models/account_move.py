from odoo import models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def post(self):
        # Itera sobre cada asiento que se intenta publicar.
        for move in self:
            # 1. Obtiene la fecha de bloqueo personalizada desde la configuración de la compañía.
            lock_date = move.company_id.sales_lock_date

            # 2. Si no hay fecha de bloqueo configurada, no hace nada.
            if not lock_date:
                continue

            # 3. La condición clave: verifica si el diario es de tipo "venta".
            if move.journal_id.type == 'sale':
                # 4. Compara la fecha del asiento con la fecha de bloqueo.
                if move.date <= lock_date:
                    # 5. Si la condición se cumple, lanza un error y detiene el proceso.
                    raise UserError(
                        _("No puedes publicar asientos de venta en o antes de la fecha de bloqueo (%s) porque el diario de ventas está cerrado.", lock_date)
                    )

        # Llama a la función original de Odoo para que ejecute todas las demás validaciones (incluyendo tax_lock_date).
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