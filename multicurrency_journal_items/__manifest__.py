{
    'name': 'Multicurrency Journal Items',
    'version': '1.0',
    'depends': ['account'],
    'depends': ['base', 'account', 'analytic'],
    'license': 'LGPL-3',
    'author': 'Newcom LCS',
    'data': [
        'views/account_move_line_views.xml',
        'views/res_company_views.xml',
        'views/account_analytic_line_views_extension.xml',
        'views/account_analytic_views.xml',
    ],
}