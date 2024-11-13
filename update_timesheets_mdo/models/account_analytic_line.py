from odoo import models, fields, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def update_analytic_lines(self):
        # Fetch the financial account ID
        financial_account = self.env['account.account'].search([('code', '=', '5.1.2.01.110')], limit=1)
        if not financial_account:
            raise ValueError("Financial account '5.1.2.01.110 Honorarios Producción' not found.")

        # Fetch USD currency
        usd_currency = self.env.ref('base.USD')
        if not usd_currency:
            raise ValueError("USD currency not found.")

        # Find analytic lines that match the criteria
        analytic_lines = self.search([
            ('employee_id', '!=', False),
            ('general_account_id', '=', False)
        ])

        # Update each analytic line
        for line in analytic_lines:
            # Fetch the exchange rate for the line's date
            rate = self.env['res.currency']._get_conversion_rate(line.currency_id, usd_currency, self.env.company, line.date)
            
            # Convert the amount to USD
            amount_in_usd = line.amount * rate
            line.amount_second_currency = amount_in_usd
            
            # Print the converted amount
            print(f"Converted amount for line {line.id}: {amount_in_usd} USD")

        # Update the general_account_id field
        analytic_lines.write({'general_account_id': financial_account.id})
