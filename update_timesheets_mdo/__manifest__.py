{
    'name': 'My Custom Module',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom module to update analytic lines',
    'license': 'LGPL-3',
    'author': 'Newcom LCS',
    'description': 'Updates the general_account_id for analytic lines daily.',
    'depends': ['account'],
    'data': [
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
}
