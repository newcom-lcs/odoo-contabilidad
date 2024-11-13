# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger('newcomlog')

class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    # Many2one relation linking back to account.analytic.account
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account"
    )
    

    custom_budget_currency_option = fields.Selection(
        selection=[
            ('company_currency', 'Moneda Principal'),
            ('other_currency', 'Moneda Secundaria'),
        ],
        string="Moneda del presupuesto",
        default='company_currency',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )



class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    planned_amount = fields.Monetary(compute='_compute_planned_amount')
    
    custom_planned_amount = fields.Monetary(
        compute='_compute_custom_planned_amount',
        string='Importe Previsto (USD)',
        store=True,
        required=True,
        default=0,
        help="Amount you plan to earn/spend. Record a positive amount if it is a revenue and a negative amount if it is a cost.",
        inverse="_inverse_custom_planned_amount"
    )
    custom_practical_amount = fields.Monetary(
        compute='_compute_custom_practical_amount',
        string='Importe Real (USD)',
        help="Amount really earned/spent.",
    )
    custom_theoritical_amount = fields.Monetary(
        compute='_compute_custom_theoritical_amount',
        string='Importe Teórico (USD)',
        help="Amount you are supposed to have earned/spent at this date.",
    )
    
    custom_percentage = fields.Float(
        string='Logro (USD)',
        compute='_compute_custom_percentage',
        store=True
    )

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # overrides the default read_group in order to compute the computed fields manually for the group

        fields_list = {'custom_practical_amount', 'custom_theoritical_amount'}

        # Not any of the fields_list support aggregate function like :sum
        def truncate_aggr(field):
            field_no_aggr = field.split(':', 1)[0]
            if field_no_aggr in fields_list:
                return field_no_aggr
            return field
        fields = {truncate_aggr(field) for field in fields}

        # Read non fields_list fields
        result = super(CrossoveredBudgetLines, self).read_group(
            domain, list(fields - fields_list), groupby, offset=offset,
            limit=limit, orderby=orderby, lazy=lazy)

        # Populate result with fields_list values
        if fields & fields_list:
            for group_line in result:

                # initialise fields to compute to 0 if they are requested
                if 'custom_practical_amount' in fields:
                    group_line['custom_practical_amount'] = 0
                if 'custom_theoritical_amount' in fields:
                    group_line['custom_theoritical_amount'] = 0

                domain = group_line.get('__domain') or domain
                all_budget_lines_that_compose_group = self.search(domain)

                for budget_line_of_group in all_budget_lines_that_compose_group:
                    if 'custom_practical_amount' in fields:
                        group_line['custom_practical_amount'] += budget_line_of_group.custom_practical_amount

                    if 'custom_theoritical_amount' in fields:
                        group_line['custom_theoritical_amount'] += budget_line_of_group.custom_theoritical_amount
        return result

    @api.depends('planned_amount')
    def _compute_custom_planned_amount(self):
        for line in self:
            currency_id = line.company_id.currency_id
            second_currency_id = line.company_id.second_currency_id
            line.custom_planned_amount = 0.0
            if line.planned_amount and currency_id.id != second_currency_id.id:
                line.custom_planned_amount = currency_id._convert(line.planned_amount, second_currency_id, line.company_id, line.date_from or fields.Date.today())
            else:
                line.custom_planned_amount = line.planned_amount

    def _inverse_custom_planned_amount(self):
        for line in self:
            currency_id = line.company_id.currency_id
            second_currency_id = line.company_id.second_currency_id
            if line.custom_planned_amount and currency_id.id != second_currency_id.id:
                line.planned_amount = second_currency_id._convert(line.custom_planned_amount, currency_id, line.company_id, line.date_from or fields.Date.today())
            else:
                line.planned_amount = line.custom_planned_amount

    @api.depends('custom_planned_amount')
    def _compute_planned_amount(self):
        for line in self:
            currency_id = line.company_id.currency_id
            second_currency_id = line.company_id.second_currency_id
            line.planned_amount = 0.0
            if line.custom_planned_amount and currency_id.id != second_currency_id.id:
                line.planned_amount = second_currency_id._convert(line.custom_planned_amount, currency_id, line.company_id, line.date_from or fields.Date.today())
            else:
                line.planned_amount = line.custom_planned_amount
            

    def _inverse_planned_amount(self):
        for line in self:
            currency_id = line.company_id.currency_id
            second_currency_id = line.company_id.second_currency_id
            if line.planned_amount and currency_id.id != second_currency_id.id:
                line.custom_planned_amount = currency_id._convert(line.planned_amount, second_currency_id, line.company_id, line.date_from or fields.Date.today())
                _logger.info(line.custom_planned_amount)
            else:
                line.custom_planned_amount = line.planned_amount

    
    @api.depends('practical_amount')
    def _compute_custom_practical_amount(self):
        for line in self:
            currency_id = line.company_id.currency_id
            second_currency_id = line.company_id.second_currency_id

            acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            amount_in_budget_curr = 0.0
            if line.analytic_account_id.id:
                analytic_line_obj = self.env['account.analytic.line']
                domain = [('account_id', '=', line.analytic_account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids)]
                
                analytic_line_ids = analytic_line_obj.search(domain)
                for analytic_line_id in analytic_line_ids:
                    amount_in_budget_curr += currency_id._convert(analytic_line_id.amount, second_currency_id, line.company_id, analytic_line_id.date)
            else:
                aml_obj = self.env['account.move.line']
                domain = [('account_id', 'in',
                           line.general_budget_id.account_ids.ids),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ('move_id.state', '=', 'posted')
                          ]
                account_move_line_ids = aml_obj.search(domain)
                for account_move_line_id in account_move_line_ids:
                    acc_move_line_amount = account_move_line_id.credit - account_move_line_id.debit
                    amount_in_budget_curr += currency_id._convert(acc_move_line_amount, second_currency_id, line.company_id, account_move_line_id.date)

            line.custom_practical_amount = amount_in_budget_curr

    @api.depends('date_from', 'date_to')
    def _compute_custom_theoritical_amount(self):
        today = fields.Date.today()
        for line in self:
            if line.paid_date:
                if today <= line.paid_date:
                    theo_amt = 0.00
                else:
                    theo_amt = line.custom_planned_amount
            else:
                if not line.date_from or not line.date_to:
                    raise ValidationError(_('Debe especificar el Período del presupuesto!'))
                    line.theoritical_amount = 0
                    continue
                
                # One day is added since we need to include the start and end date in the computation.
                # For example, between April 1st and April 30th, the timedelta must be 30 days.
                
                line_timedelta = line.date_to - line.date_from + timedelta(days=1)
                elapsed_timedelta = today - line.date_from + timedelta(days=1)

                if elapsed_timedelta.days < 0:
                    # If the budget line has not started yet, theoretical amount should be zero
                    theo_amt = 0.00
                elif line_timedelta.days > 0 and today < line.date_to:
                    # If today is between the budget line date_from and date_to
                    theo_amt = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.custom_planned_amount
                else:
                    theo_amt = line.custom_planned_amount
            line.custom_theoritical_amount = theo_amt

    @api.depends('custom_theoritical_amount', 'custom_practical_amount')
    def _compute_custom_percentage(self):
        for line in self:
            # Check if planned amount is not zero to avoid division by zero
            if line.custom_planned_amount != 0:
                line.custom_percentage = (line.custom_practical_amount / line.custom_theoritical_amount)
            else:
                line.custom_percentage = 0.0

#    def create(self, vals):
#        for v in vals:
#            v['planned_amount'] = v['custom_planned_amount']
        
#        raise ValidationError(vals)
#        res = super(CrossoveredBudgetLines, self).create(vals)
#        return res

