from odoo import models

from odoo.exceptions import UserError
# import logging
# import json
# import requests
# from dateutil.relativedelta import relativedelta
# _logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def get_agip_data(self, partner, date):
        raise UserError(_(
            'cosito del coso '
            'AGIP'))
