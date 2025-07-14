from odoo import models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscalyear_lock_date(self):
        res = super()._check_fiscalyear_lock_date()
        for move in self:
            if move.journal_id == 'sale':
                lock_date_sales = move.company_id._get_user_sales_lock_date()
                if lock_date_sales and move.date <= lock_date_sales:
                    if self.user_has_groups('account.group_account_manager'):
                        message = _("You cannot add/modify entries prior to and inclusive of the lock date %s.", format_date(self.env, lock_date_sales))
                    else:
                        message = _("Entries cannot be added or modified before the sales journal lock date %s, inclusive. Please check your company settings or consult an advisor.", format_date(self.env, lock_date_sales))
                    raise UserError(message)
        return res