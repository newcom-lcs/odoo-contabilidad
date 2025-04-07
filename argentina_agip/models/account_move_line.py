from odoo import models
import logging

_logger = logging.getLogger()

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    def _compute_all_tax(self):
                
        for line in self:
            super(AccountMoveLine, line)._compute_all_tax()
