from odoo import models

class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscalyear_lock_date(self):
        res = super()._check_fiscalyear_lock_date()
        for move in self:
            lock_date_sales = move.company_id._get_user_sales_lock_date()
            if move.date <= lock_date_sales:
                if self.user_has_groups('account.group_account_manager'):
                    message = _("You cannot add/modify entries prior to and inclusive of the lock date %s.", format_date(self.env, lock_date))
                else:
                    message = _("Entries cannot be added or modified before the sales journal lock date %s, inclusive. Please check your company settings or consult an advisor.", format_date(self.env, lock_date))
                raise UserError(message)

        return res