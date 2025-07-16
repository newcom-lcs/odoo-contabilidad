from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

class AccountMove(models.Model):
    _inherit = "account.move"
    #sale_lock_date_message = fields.Char(compute='_compute_sale_lock_date_message')


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
    
    # @api.depends('date', 'line_ids.debit', 'line_ids.credit', 'line_ids.tax_line_id', 'line_ids.tax_ids', 'line_ids.tax_tag_ids',
    #              'invoice_line_ids.debit', 'invoice_line_ids.credit', 'invoice_line_ids.tax_line_id', 'invoice_line_ids.tax_ids', 'invoice_line_ids.tax_tag_ids')
    # def _compute_sale_lock_date_message(self):
    #     for move in self:
    #         accounting_date = move.date or fields.Date.context_today(move)
    #         affects_tax_report = move._affect_tax_report()
    #         move.sale_lock_date_message = move._get_lock_date_message(accounting_date, affects_tax_report)

    def _get_violated_lock_dates(self, invoice_date, has_tax):
        locks = super()._get_violated_lock_dates(invoice_date, has_tax)
        sale_lock_date = self.company_id._get_user_sales_lock_date()
        if invoice_date and sale_lock_date and invoice_date <= sale_lock_date:
            locks.append((sale_lock_date, _('sales')))
        locks.sort()
        return locks

    # def _get_lock_date_message(self, invoice_date, has_tax):
    #     lock_dates = self._get_violated_lock_dates(invoice_date, has_tax)
    #     if lock_dates:
    #         invoice_date = self._get_accounting_date(invoice_date, has_tax)
    #         lock_date, lock_type = lock_dates[-1]
    #         tax_lock_date_message = _(
    #             "The date is being set prior to the %(lock_type)s lock date %(lock_date)s. "
    #             "The Journal Entry will be accounted on %(invoice_date)s upon posting.",
    #             lock_type=lock_type,
    #             lock_date=format_date(self.env, lock_date),
    #             invoice_date=format_date(self.env, invoice_date))
    #         return tax_lock_date_message
    #     return False