from odoo import models, fields

from odoo.exceptions import UserError
import json
import requests
from dateutil.relativedelta import relativedelta
import logging


_logger = logging.getLogger()


class ResCompany(models.Model):
    _inherit = "res.company"

    def get_agip_data(self, partner, date):
        """ Obtener alícuotas desde API de AGIP de Newcom
        :param partner: El partner sobre el cual trabajamos
        :param date: La fecha del comprobante
        Devuelve diccionario de datos
        """
        vat = partner.vat.replace("-","")
        
        alicuota_percepcion = 0.0
        alicuota_retencion = 0.0
        numero_comprobante = False
        
        _logger.info('Obteniendo datos de AGIP para el partner %s' % vat)
        date_date = fields.Date.from_string(date)

        # Establecer parámetros de solicitud
        url = "https://srv752591.hstgr.cloud/api/v1/agip/"+vat
        headers = {'content-type': 'application/json'}

        # Realizar solicitud
        r = requests.get(url, headers=headers)
        json_body = r.json()
        _logger.info('recibida respuesta: \n\n%s' % json_body)

        if r.status_code == 200:
            data = json_body.get("data")            
            alicuota_percepcion = data.get("per")
            alicuota_retencion = data.get("ret")
            numero_comprobante = vat

        data = {
            'alicuota_percepcion': alicuota_percepcion,
            'alicuota_retencion': alicuota_retencion,
            'numero_comprobante': numero_comprobante,
        }


        _logger.info("We've got the following data: \n%s" % data)

        return data

    def get_partner_alicuot(self, partner, date, line=None):
        _logger.info("get_partner_alicuot %s ", partner, date)
        self.ensure_one()
        commercial_partner = partner.commercial_partner_id
        from_date = date + relativedelta(day=1)
        to_date = date + relativedelta(day=1, days=-1, months=+1)
        
        agip_tag = self.env.ref('l10n_ar_ux.tag_tax_jurisdiccion_901')
        arba_tag = self.env.ref('l10n_ar_ux.tag_tax_jurisdiccion_902')
        cdba_tag = self.env.ref('l10n_ar_ux.tag_tax_jurisdiccion_904')
    
        if arba_tag:
            arba_data = self.get_arba_data(
                commercial_partner,
                from_date, to_date,
            )
            # si no hay numero de comprobante entonces es porque no
            # figura en el padron, aplicamos alicuota no inscripto
            if not arba_data['numero_comprobante']:
                arba_data['numero_comprobante'] = \
                    'Alícuota no inscripto'
                arba_data['alicuota_retencion'] = \
                    self.arba_alicuota_no_sincripto_retencion
                arba_data['alicuota_percepcion'] = \
                    self.arba_alicuota_no_sincripto_percepcion

            arba_data['partner_id'] = commercial_partner.id
            arba_data['company_id'] = self.id
            arba_data['tag_id'] = arba_tag.id
            arba_data['from_date'] = from_date
            arba_data['to_date'] = to_date
            alicuot = partner.arba_alicuot_ids.sudo().create(arba_data)
        if agip_tag:
            agip_data = self.get_agip_data(
                commercial_partner,
                date,
            )
            # si no hay numero de comprobante entonces es porque no
            # figura en el padron, aplicamos alicuota no inscripto
            if not agip_data['numero_comprobante']:
                agip_data['numero_comprobante'] = \
                    'Alícuota no inscripto'
                agip_data['alicuota_retencion'] = \
                    self.agip_alicuota_no_sincripto_retencion
                agip_data['alicuota_percepcion'] = \
                    self.agip_alicuota_no_sincripto_percepcion
            agip_data['from_date'] = from_date
            agip_data['to_date'] = to_date
            agip_data['partner_id'] = commercial_partner.id
            agip_data['company_id'] = self.id
            agip_data['tag_id'] = agip_tag.id
            alicuot = partner.arba_alicuot_ids.sudo().create(agip_data)
        # if cdba_tag:
        #     cordoba_data = self.get_cordoba_data(
        #         commercial_partner,
        #         date,
        #     )
        #     cordoba_data['from_date'] = from_date
        #     cordoba_data['to_date'] = to_date
        #     cordoba_data['partner_id'] = commercial_partner.id
        #     cordoba_data['company_id'] = self.id
        #     cordoba_data['tag_id'] = cdba_tag.id
        #     alicuot = partner.arba_alicuot_ids.sudo().create(cordoba_data)
        return alicuot