from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
# from odoo.tools.misc import formatLang
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re

#########
# helpers
#########


def format_amount(amount, padding=15, decimals=2, sep=""):
    if amount < 0:
        template = "-{:0>%dd}" % (padding - 1 - len(sep))
    else:
        template = "{:0>%dd}" % (padding - len(sep))
    res = template.format(
        int(round(abs(amount) * 10**decimals, decimals)))
    if sep:
        res = "{0}{1}{2}".format(res[:-decimals], sep, res[-decimals:])
    return res


def get_line_tax_base(move_line):
    return sum(move_line.move_id.line_ids.filtered(
        lambda x: move_line.tax_line_id in x.tax_ids).mapped(
        'balance'))


def get_pos_and_number(full_number):
    """
    Para un numero nos fijamos si hay '-', si hay:
    * mas de 1, entonces devolvemos error
    * 1, entonces devolvemos las partes (solo parte númerica)
    * 0, entonces devolvemos '0' y parte númerica del número que se pasó
    """
    args = full_number.split('-')
    if len(args) == 1:
        # si no hay '-' tomamos punto de venta 0
        return ('0', re.sub('[^0-9]', '', args[0]))
    else:
        return re.sub('[^0-9]', '', args[0]), re.sub('[^0-9]', '', ''.join(args[1:]))


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def iibb_aplicado_api_files_values(self, move_lines):
        """ Implementado segun especificación en carpeta doc de este repo
        """
        def format_amount(amount, integers, decimals=2):
            # overwrite default format_amount
            template = "%0" + "%ss" % (integers + decimals + 1)
            # TODO se podria mejorar haciendo algo asi pero hace falta
            # hacer parametro el 16
            # "{0:>16.2f}".format(12.1)
            return template % "{0:.2f}".format(
                round(amount, decimals)).replace('.', ',')
        self.ensure_one()
        ret = ''
        perc = ''

        for line in move_lines:
            partner = line.partner_id

            tax = line.tax_line_id

            alicuot_line = tax.get_partner_alicuot(partner, line.date)
            if not alicuot_line:
                raise ValidationError(_(
                    'No hay alicuota configurada en el partner '
                    '"%s" (id: %s)') % (partner.name, partner.id))

            # 1 - tipo de operacion
            if tax.type_tax_use in ['sale', 'purchase'] and \
                    tax.amount_type == 'partner_tax':
                content = '2'
                alicuot = alicuot_line.alicuota_percepcion

                # para percepciones ho es obligatorio
                articulo_inciso_calculo = \
                    alicuot_line.api_articulo_inciso_calculo_percepcion \
                    or '000'
                articulo_inciso_retiene = \
                    alicuot_line.api_codigo_articulo_percepcion
            elif tax.type_tax_use in ['customer', 'supplier'] and \
                    tax.withholding_type == 'partner_tax':
                content = '1'
                alicuot = alicuot_line.alicuota_retencion

                articulo_inciso_calculo = \
                    alicuot_line.api_articulo_inciso_calculo_retencion
                articulo_inciso_retiene = \
                    alicuot_line.api_codigo_articulo_retencion
            else:
                raise ValidationError(_(
                    'Tipo de impuesto %s equivocado. Se aceptan solo '
                    'percepciones o retenciones con "Cálculo de impuestos" '
                    'igual a "Alícuota en el Partner". Id de impuestos '
                    '"%s"') % (tax.tax_group_id.name, tax.id))

            if not articulo_inciso_calculo or not articulo_inciso_retiene:
                raise ValidationError(_(
                    'Debe setear la información de "artículo/inciso" en las'
                    ' alícutoas de contacto %s') % partner.name)

            # 2 - fecha
            content += fields.Date.from_string(line.date).strftime('%d/%m/%Y')

            # 3 - Código de artículo Inciso por el que retiene
            content += articulo_inciso_retiene

            # 4 - tipo de comprobante y
            # 5 - letra de comprobante
            internal_type = line.l10n_latam_document_type_id.internal_type
            move = line.move_id

            if internal_type in ('invoice'):
                # factura
                content += '01' + line.l10n_latam_document_type_id.l10n_ar_letter

            elif internal_type == 'debit_note':
                # ND
                content += '02' + line.l10n_latam_document_type_id.l10n_ar_letter
            elif internal_type == 'credit_note':
                content += '10' + line.l10n_latam_document_type_id.l10n_ar_letter
            else:
                # orden de pago (sin letra)
                # 09 sería otro comprobante y 10 reinitegro de perc/ret
                # aclaración: si cargo una nota de crédito con código 10 me aparece un mensaje como este:
                # "Error: Línea 25: Debe ingresar un tipo de comprobante válido. 
                # La carga de Reintegro de Retenc./Perc solo se puede efectuar desde el formulario en forma manual. La línea fue descartada."
                content += '03 '

            # 6 - numero comprobante Texto(16)
            if internal_type in ('invoice', 'credit_note', 'debit_note'):
                # TODO el aplicativo deberia empezar a aceptar 5 digitos
                pos, number = get_pos_and_number(move.l10n_latam_document_number)
                # versión 4.0 de siprib release 0 no acepta 5 dígitos aún
                content += '{:>03s}'.format(pos)[-4:]
                content += '{:>08s}'.format(number)
                content += '    '
            else:
                content += '%016s' % (move.l10n_latam_document_number or '')

            # 7 - fecha comprobante
            content += fields.Date.from_string(move.date).strftime('%d/%m/%Y')

            # 8 - monto comprobante
            content += format_amount(abs(line.move_id.amount_total_signed), 12, 2) if line.move_id.is_invoice() else format_amount(abs(-line.balance), 12, 2)

            # 9 - tipo de documento
            # nosotros solo permitimos CUIT por ahora
            # Revisar
            content += '3'

            # 10 - numero de documento
            content += partner.ensure_vat()

            # 11 - Condición frente a Ingresos Brutos
            # 1 es inscripto, 2 no inscripto con oblig. a insc y 3 no insc sin
            # oblig a insc. TODO implementar 2
            gross_income_type = partner.l10n_ar_gross_income_type
            if not gross_income_type:
                raise ValidationError(_(
                    'Debe setear el tipo de inscripción de IIBB del partner '
                    '"%s" (id: %s)') % (
                    partner.name, partner.id))
            if gross_income_type in ['multilateral', 'local']:
                content += '1'
            else:
                content += '3'

            # 12 - Número de Inscripción en Ingresos Brutos
            content += (re.sub(
                '[^0-9]', '',
                partner.l10n_ar_gross_income_number or '')).rjust(10, '0')

            # 13 - Situación frente a IVA donde:
            # ri (1), rni (2), exento (3), monotr (4)
            res_iva = partner.l10n_ar_afip_responsibility_type_id
            if res_iva.code in ['1', '1FM']:
                # RI
                content += '1'
            elif res_iva.code == '2':
                # RNI
                content += '2'
            elif res_iva.code == '4':
                # EXENTO
                content += '3'
            elif res_iva.code == '6':
                # MONOT
                content += '4'
            else:
                raise ValidationError(_(
                    'La responsabilidad frente a IVA "%s" no está soportada '
                    'para ret/perc Santa Fe') % res_iva.name)

            # 14 - Marca inscripción Otros Gravámenes
            # TODO implementar (requiere nuevo campo en odoo?)
            content += '0'

            # 15 - Marca Inscripción DREI
            # TODO revisar si implementamos o no, aparentemente este campo
            # activo en drei no se usa o no es lo que esperamos, por ahora
            # no lo hacemos requerido para no andar molestando al dope
            # if not partner.drei:
            #     raise ValidationError(_(
            #         'Debe seleccionar situación DREI para partner '
            #         '"%s" (id: %s)') % (
            #             partner.name, partner.id))
            content += partner.drei == 'activo' and '1' or '0'

            # 16 - Importe Otros Gravámenes
            # TODO implementar
            content += format_amount(0.0, 10, 2)

            # 17 - Importe IVA (solo si factura)
            if line.move_id.is_invoice():
                amounts = line.move_id._l10n_ar_get_amounts(company_currency=True)
                vat_amount = amounts['vat_amount']
                base_amount = amounts['vat_taxable_amount']
            else:
                vat_amount = 0.0
                base_amount = line.payment_id and line.payment_id.withholdable_base_amount or 0.0
            content += format_amount(vat_amount, 10, 2)

            # 18 - Base Imponible para el cálculo
            # tal vez la base deberiamos calcularlo asi, en pagos no porque
            # los asientos estan separados
            # content += format_amount(-get_line_tax_base(line), 12, 2, ',')
            content += format_amount(base_amount, 12, 2)

            # 19 - Alícuota / alicuota
            content += format_amount(alicuot, 2, 2)

            # 20 - Impuesto Determinado
            content += format_amount(abs(-line.balance), 12, 2)

            # 21 - Derecho Registro e Inspección
            # TODO implementar
            # es un importe seguramente importe retenido de drei
            content += format_amount(0.0, 9, 2)

            # 22 - Monto Retenido
            # TODO por ahora es igual a impuesto determinado pero, podria ser
            # distinto en algún caso?
            content += format_amount(abs(-line.balance), 12, 2)

            # 23 - Artículo/Inciso para el cálculo
            content += articulo_inciso_calculo

            # 24 - Tipo de Exención
            # TODO implementar. Por ahora no implementamos excenciones ya que
            # a priori no las informan
            content += '0'

            # 25 - Año de Exención
            # TODO implementar
            content += '0000'

            # 26 - Número de Certificado de Exención
            # TODO implementar
            content += '      '

            # 27 - Número de Certificado Propio
            # TODO implementar
            content += '            '

            # new line
            content += '\r\n'

            if tax.type_tax_use in ['sale', 'purchase']:
                perc += content
            elif tax.type_tax_use in ['customer', 'supplier']:
                ret += content

        # return [
        #     {
        #         'txt_filename': 'Perc IIBB API Aplicadas.txt',
        #         'txt_content': perc,
        #     },
        #     {
        #         'txt_filename': 'Ret IIBB API Aplicadas.txt',
        #         'txt_content': ret,
        #     }
        return [
            {
                'txt_filename': 'Perc/Ret IIBB API Aplicadas.txt',
                'txt_content': perc + ret,
            }]


    def iibb_aplicado_agip_files_values(self, move_lines):
        """ Ver readme del modulo para descripcion del formato. Tambien
        archivos de ejemplo en /doc
        """
        self.ensure_one()

        if self.company_id.agip_padron_type != 'regimenes_generales':
            raise ValidationError(_(
                'Por ahora solo esta implementado el padrón de Regímenes '
                'Generales, revise la configuración en "Contabilidad / "'
                'Configuración / Ajustes"'))

        ret_perc = ''
        credito = ''

        company_currency = self.company_id.currency_id
        for line in move_lines.sorted('date'):

            # pay_group = payment.payment_group_id
            move = line.move_id
            payment = line.payment_id
            tax = line.tax_line_id
            partner = line.partner_id
            internal_type = line.l10n_latam_document_type_id.internal_type

            if not partner.vat:
                raise ValidationError(_(
                    'El partner "%s" (id %s) no tiene número de identificación '
                    'seteada') % (partner.name, partner.id))

            alicuot_line = tax.get_partner_alicuot(partner, line.move_id._found_related_invoice().date or line.date)
            if not alicuot_line:
                raise ValidationError(_(
                    'No hay alicuota configurada en el partner '
                    '"%s" (id: %s)') % (partner.name, partner.id))

            ret_perc_applied = False
            es_percepcion = False
            # 1 - Tipo de Operación
            if tax.type_tax_use in ['sale', 'purchase']:
                    # tax.amount_type == 'partner_tax':
                es_percepcion = True
                content = '2'
                alicuot = alicuot_line.alicuota_percepcion
            elif tax.type_tax_use in ['customer', 'supplier']:
                    # tax.withholding_type == 'partner_tax':
                content = '1'
                alicuot = alicuot_line.alicuota_retencion

            or_inv = line.move_id._found_related_invoice()
            
            # notas de credito
            if internal_type == 'credit_note':
                # 2 - Nro. Nota de crédito
                content += '%012d' % int(
                    re.sub('[^0-9]', '', move.l10n_latam_document_number or ''))

                # 3 - Fecha Nota de crédito
                content += fields.Date.from_string(
                    line.date).strftime('%d/%m/%Y')

                # 4 - Monto nota de crédito
                # TODO implementar devoluciones de pagos
                # content += format_amount(
                #     line.move_id.cc_amount_total, 16, 2, ',')
                # la especificacion no lo dice claro pero un errror al importar
                # si, lo que se espera es el importe base, ya que dice que
                # este, multiplicado por la alícuota, debe ser igual al importe
                # a retener/percibir
                taxable_amount = line.tax_base_amount
                content += format_amount(taxable_amount, 16, 2, ',')

                # 5 - Nro. certificado propio
                # opcional y el que nos pasaron no tenia
                content += '                '

                # segun interpretamos de los daots que nos pasaron 6, 7, 8 y 11
                # son del comprobante original
                if not or_inv:
                    raise ValidationError(_(
                        'No pudimos encontrar el comprobante original para %s '
                        '(id %s). Verifique que en la nota de crédito "%s", el'
                        ' campo origen es el número de la factura original'
                    ) % (
                        line.move_id.display_name,
                        line.move_id.id,
                        line.move_id.display_name))

                # 6 - Tipo de comprobante origen de la retención
                content += self._type_of_receipt(or_inv, es_percepcion)

                # 7 - Letra del Comprobante
                if payment:
                    content += ' '
                else:
                    content += or_inv.l10n_latam_document_type_id.l10n_ar_letter

                # 8 - Nro de comprobante (original)
                content += '%016d' % int(
                    re.sub('[^0-9]', '', or_inv.l10n_latam_document_number or ''))

                # 9 - Nro de documento del Retenido
                content += str(partner._get_id_number_sanitize())

                # 10 - Código de norma
                # por ahora solo padron regimenes generales
                content += '029'

                # 11 - Fecha de retención/percepción
                content += fields.Date.from_string(
                    or_inv.invoice_date).strftime('%d/%m/%Y')

                # 12 - Ret/percep a deducir

                # si la línea tiene moneda diferente de la moneda de la compañía queremos que la ret/perc
                # se calcule aplicando la alícuota sobre la base imponible en la moneda de la compañía
                if line.currency_id and line.currency_id != line.company_id.currency_id:
                    ret_perc_applied = float_round((taxable_amount*alicuot/100), precision_digits=2)
                content += format_amount((line.balance if not ret_perc_applied else ret_perc_applied), 16, 2, ',')

                # 13 - Alícuota
                #Como siempre usamos codigo de normal 29, puede ser 0
                content += format_amount(alicuot, 5, 2, ',')

                content += '\r\n'

                credito += content
                continue

            # 2 - Código de Norma
            # por ahora solo padron regimenes generales
            content += '029'

            # 3 - Fecha de retención/percepción
            content += fields.Date.from_string(line.date).strftime('%d/%m/%Y')

            # 4 - Tipo de comprobante origen de la retención
            if internal_type == 'invoice':
                content += '10' if line.move_id.l10n_latam_document_type_id.code in ['201', '206', '211'] else '01'
            elif internal_type == 'debit_note':
                if es_percepcion:
                    content += '09'
                else:
                    content += '02'
            else:
                # orden de pago
                content += '03'

            # 5 - Letra del Comprobante
            # segun vemos en los archivos de ejemplo solo en percepciones
            if payment:
                content += ' '
            else:
                if not line.l10n_latam_document_type_id:
                    raise ValidationError(_(
                        'No hay tipo de documento configurado para la línea %s') % line.name)
                letter = line.l10n_latam_document_type_id.l10n_ar_letter
                if not isinstance(letter, str):
                    raise ValidationError(_(
                        'El tipo de documento %s no tiene una letra válida configurada') % 
                        line.l10n_latam_document_type_id.name)
                content += letter

            # 6 - Nro de comprobante
            content += '%016d' % int(
                re.sub('[^0-9]', '', move.l10n_latam_document_number or ''))

            # 7 - Fecha del comprobante
            content += fields.Date.from_string(move.date).strftime('%d/%m/%Y')

            # obtenemos montos de los comprobantes
            payment_group = line.payment_id.payment_group_id
            if payment_group:
                # solo en comprobantes A, M segun especificacion
                vat_amount = 0.0
                total_amount = float_round(payment_group.payments_amount, precision_digits=2)
                # es lo mismo que payment_group.matched_amount_untaxed
                taxable_amount = float_round(payment.withholdable_base_amount, precision_digits=2)

                # lo sacamos por diferencia
                other_taxes_amount = company_currency.round(
                    total_amount - taxable_amount - vat_amount)
            elif line.move_id.is_invoice():
                amounts = line.move_id._l10n_ar_get_amounts(company_currency=True)
                # segun especificacion el iva solo se reporta para estos
                if line.l10n_latam_document_type_id.l10n_ar_letter in ['A', 'M']:
                    vat_amount = amounts['vat_amount']
                else:
                    vat_amount = 0.0

                total_amount = (1 if line.move_id.is_inbound() else -1) * line.move_id.amount_total_signed

                # por si se olvidaron de poner agip en una linea de factura
                # la base la sacamos desde las lineas de impuesto
                # taxable_amount = line.move_id.cc_amount_untaxed
                taxable_amount = line.tax_base_amount

                # tambien lo sacamos por diferencia para no tener error (por el
                # calculo trucado de taxable_amount por ejemplo) y
                # ademas porque el iva solo se reporta si es factura A, M
                other_taxes_amount = company_currency.round(
                    total_amount - taxable_amount - vat_amount)
                # other_taxes_amount = line.move_id.cc_other_taxes_amount
            else:
                raise ValidationError(_('El impuesto no está asociado'))

            # 8 - Monto del comprobante
            content += format_amount(total_amount, 16, 2, ',')

            # 9 - Nro de certificado propio
            content += (payment.withholding_number or '').rjust(16, ' ')

            # 10 - Tipo de documento del Retenido
            # vat
            if partner.l10n_latam_identification_type_id.name not in ['CUIT', 'CUIL', 'CDI']:
                raise ValidationError(_(
                    'EL el partner "%s" (id %s), el tipo de identificación '
                    'debe ser una de siguientes: CUIT, CUIL, CDI.' % (partner.id, partner.name)))
            doc_type_mapping = {'CUIT': '3', 'CUIL': '2', 'CDI': '1'}
            content += doc_type_mapping[partner.l10n_latam_identification_type_id.name]

            # 11 - Nro de documento del Retenido
            content += str(partner._get_id_number_sanitize())

            # 12 - Situación IB del Retenido
            # 1: Local 2: Convenio Multilateral
            # 4: No inscripto 5: Reg.Simplificado
            if not partner.l10n_ar_gross_income_type:
                raise ValidationError(_(
                    'Debe setear el tipo de inscripción de IIBB del partner '
                    '"%s" (id: %s)') % (partner.name, partner.id))

            # ahora se reportaria para cualquier inscripto el numero de cuit
            gross_income_mapping = {
                'local': '5', 'multilateral': '2', 'exempt': '4'}
            content += gross_income_mapping[partner.l10n_ar_gross_income_type]

            # 13 - Nro Inscripción IB del Retenido
            if partner.l10n_ar_gross_income_type == 'exempt':
                content += '00000000000'
            else:
                content += partner.ensure_vat()

            # 14 - Situación frente al IVA del Retenido
            # 1 - Responsable Inscripto
            # 3 - Exento
            # 4 - Monotributo
            res_iva = partner.l10n_ar_afip_responsibility_type_id
            if res_iva.code in ['1', '1FM']:
                # RI
                content += '1'
            elif res_iva.code == '4':
                # EXENTO
                content += '3'
            elif res_iva.code == '6':
                # MONOT
                content += '4'
            else:
                raise ValidationError(_(
                    'La responsabilidad frente a IVA "%s" no está soportada '
                    'para ret/perc AGIP') % res_iva.name)

            # 15 - Razón Social del Retenido
            content += '{:30.30}'.format(partner.name)

            # 16 - Importe otros conceptos
            content += format_amount(other_taxes_amount, 16, 2, ',')

            # 17 - Importe IVA
            content += format_amount(vat_amount, 16, 2, ',')

            # 18 - Monto Sujeto a Retención/ Percepción
            content += format_amount(taxable_amount, 16, 2, ',')

            # 19 - Alícuota
            # Puede ser 00,00 ya que nosotros siempre usamos 29 como Código de Norma
            content += format_amount(alicuot, 5, 2, ',')

            # 20 - Retención/Percepción Practicada

            # si la línea tiene moneda diferente de la moneda de la compañía queremos que la ret/perc
            # se calcule aplicando la alícuota sobre la base imponible en la moneda de la compañía
            if line.currency_id and line.currency_id != line.company_id.currency_id:
                ret_perc_applied = float_round((taxable_amount*alicuot/100), precision_digits=2)
            content += format_amount((-line.balance if not ret_perc_applied else ret_perc_applied), 16, 2, ',')

            # 21 - Monto Total Retenido/Percibido
            content += format_amount((-line.balance if not ret_perc_applied else ret_perc_applied), 16, 2, ',')

            # 22 - Aceptacion
            content += ' '

            # 23 - Fecha Aceptación "Expresa"
            content += '          '

            content += '\r\n'

            ret_perc += content


        return [{
                'txt_filename': 'Perc/Ret IIBB AGIP Aplicadas.txt',
                'txt_content': ret_perc,
                }, {
                'txt_filename': 'NC Perc/Ret IIBB AGIP Aplicadas.txt',
                'txt_content': credito,
                }]

    @api.model
    def _type_of_receipt(self, or_inv, es_percepcion):
        code = '09'
        """
        No implementado 15-05-2024
        03- Orden de Pago (Retenciones)
        04- Boleta de Depósito (Retenciones)
        05- Liquidación de pago (Retenciones)
        06- Certificado de obra (Retenciones)
        08- Cont de Loc de Servic. (Retenciones)
        12- Orden de Pago de Comp. Electrónica MiPyMEs (Retenciones)
        """
        
        #Identificamos si el comprobante de origen es una Facturas
        #(Es el mismo codigo para percepciones y retenciones)
        if or_inv.l10n_latam_document_type_id.code in ['1', '6', '11']:
            code = '01'

        #Identificamos si el comprobante de origen es una Factura de credito MiPyMEs
        #(Es el mismo codigo para percepciones y retenciones)
        elif or_inv.l10n_latam_document_type_id.code in ['201', '206', '211']:
            code = '10'

        #Identificamos si el comprobante de Otro comprobante electronico MiPyMEs
        #(Es el mismo codigo para percepciones y retenciones)
        elif or_inv.l10n_latam_document_type_id.code in ['203', '208', '213']:
            code = '13'

        elif not es_percepcion:
        #Retenciones
            
            #Identificamos si el comprobante de origen es una Nota de debito
            if or_inv.l10n_latam_document_type_id.code in ['2', '7', '12', '52']:
                code = '02'
            
            #Identificamos si el comprobante de origen es un Recibo
            if or_inv.l10n_latam_document_type_id.code in ['4', '9', '15', '54']:
                code = '07'

            #Identificamos si el comprobante de origen es un Nota de debito electronica MiPyMEs
            if or_inv.l10n_latam_document_type_id.code in ['202', '207', '212']:
                code = '11'

        return code
