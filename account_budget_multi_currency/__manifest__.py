# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Budget with Multi Currency',
    'version': '2.1.2',
    'price': 59.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Accounting/Accounting',
    'summary': 'Multi Currency Account Budget',
    'description': """
Account Budget Multi Currency
    """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'support': 'contact@probuse.com',
    'website': 'www.probuse.com',
    'depends': [
        'account_budget',
        'project'
    ],
    'images': ['static/description/image.png'],
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/account_budget_multi_currency/1207',
    'data': [
        'views/account_budget_view.xml',
        'views/account_budget_analysis_view.xml',
        'views/account_analytic_account_views.xml',
     ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
