from odoo import models, fields

from odoo.exceptions import UserError
import logging
import json
import requests
_logger = logging.getLogger()


class ResCompany(models.Model):
    _inherit = "res.company"

    def get_agip_data(self, partner, date):
        """ Obtener alícuotas desde API de AGIP de Newcom
        :param partner: El partner sobre el cual trabajamos
        :param date: La fecha del comprobante
        Devuelve diccionario de datos
        """
        vat = partner.vat
        
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
