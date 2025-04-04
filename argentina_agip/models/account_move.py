from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger()


class AccountMove(models.Model):
    _inherit = "account.move"

    def compute_withholdings(self):
        # recorro todos las alicuotas del partner
        for alicuota in self.partner_id.arba_alicuot_ids:
            # _logger.info("tag: %s", alicuota.tag_id.id)

            # busco todos los impuestos que contienen los tags de las alicuotas del partner
            repartition_lines = self.env['account.tax.repartition.line'].search([('tag_ids', '=', alicuota.tag_id.id)])
            taxes = repartition_lines.mapped('tax_id')

            # aplico los impuestos a las lineas de la factura
            for tax in taxes:
                for line in self.line_ids:
                    line.tax_ids = line.tax_ids | taxes
                    # line._compute_all_tax()
    
        # self.write({'line_ids': self.line_ids})

        
        # self._compute_tax_totals()
        # self.recompute()