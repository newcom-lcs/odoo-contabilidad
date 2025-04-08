from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
import logging

_logger = logging.getLogger()


class AccountMove(models.Model):
    _inherit = "account.move"
    
    def compute_partner_withholdings(self):
        _logger.info("compute_partner_withholdings")

        date = self.invoice_date
        if not date:
            date = fields.Date.context_today(self)
        
        company = self.company_id
        partner = self.partner_id

        alicuotas = partner.arba_alicuot_ids.search([
            ('company_id', '=', company.id),
            ('partner_id', '=', partner.id),
            '|',
            ('from_date', '=', False),
            ('from_date', '<=', date),
            '|',
            ('to_date', '=', False),
            ('to_date', '>=', date),
        ])

        if not alicuotas:
            company.get_partner_alicuot(self.partner_id,  date)
            alicuotas = partner.arba_alicuot_ids.search([
                ('company_id', '=', company.id),
                ('partner_id', '=', partner.id),
                '|',
                ('from_date', '=', False),
                ('from_date', '<=', date),
                '|',
                ('to_date', '=', False),
                ('to_date', '>=', date),
            ])
       
        # recorro todos las alicuotas del partner
        for alicuota in alicuotas:
            # busco todos los impuestos que contienen los tags de las alicuotas del partner
            repartition_lines = self.env['account.tax.repartition.line'].search([('tag_ids', '=', alicuota.tag_id.id)])
            taxes = repartition_lines.mapped('tax_id').filtered(lambda tax: tax.active and tax.type_tax_use == 'sale')
            _logger.info(taxes)

            
            # aplico los impuestos a las lineas de la factura
            for tax in taxes:
                if alicuota.alicuota_percepcion > 0.00:
                    for line in self.invoice_line_ids:
                        line.tax_ids = line.tax_ids | taxes
                        

    # def _compute_tax_totals(self):
    #     _logger.info("_compute_tax_totals")
    #     return super()._compute_tax_totals()



