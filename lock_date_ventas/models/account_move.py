from odoo import models, _, api, fields
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscalyear_lock_date(self):
        for move in self:
            if move.journal_id.type == 'sale':
                lock_date_sales = move.company_id._get_user_sales_lock_date()
                if lock_date_sales and move.date <= lock_date_sales:
                    if self.user_has_groups('account.group_account_manager'):
                        message = _("No se puede agregar/modificar documentos con fecha anterior a la de bloqueo %s.", format_date(self.env, lock_date_sales))
                    else:
                        message = _("No se pueden agregar ni modificar entradas antes de la fecha de cierre del diario de ventas %s, inclusive. Revise la configuración de su empresa o consulte con un asesor.", format_date(self.env, lock_date_sales))
                    raise UserError(message)
        res = super()._check_fiscalyear_lock_date()
        return res

    def _get_violated_lock_dates_for_sales(self, invoice_date, has_tax):
        locks = super()._get_violated_lock_dates(invoice_date, has_tax)
        sale_lock_date = self.company_id._get_user_sales_lock_date()
        if invoice_date and sale_lock_date and invoice_date <= sale_lock_date:
            locks.append((sale_lock_date, _('sales')))
        locks.sort()
        return locks

    def _get_lock_date_message(self, invoice_date, has_tax):
        for move in self:
            if move.journal_id.type == 'sale':
                lock_dates = self._get_violated_lock_dates_for_sales(invoice_date, has_tax)
                if lock_dates:
                    lock_date, lock_type = lock_dates[-1]
                    tax_lock_date_message = _(
                        "The date is being set prior to the %(lock_type)s lock date %(lock_date)s. "
                        "Ingrese una fecha de factura posterior al %(lock_date)s",
                        lock_type=lock_type,
                        lock_date=format_date(self.env, lock_date),
                        )
                    return tax_lock_date_message
            
            return super()._get_lock_date_message(invoice_date, has_tax)
    
    @api.depends('date', 'auto_post')
    def _compute_hide_post_button(self):
        super()._compute_hide_post_button()
        for record in self:
            accounting_date = record.date or fields.Date.context_today(record)            
            has_tax = record._affect_tax_report()
            lock_dates = self._get_violated_lock_dates_for_sales(accounting_date, has_tax)
            record.hide_post_button = record.hide_post_button or \
            (record.journal_id.type == 'sale' and lock_dates)