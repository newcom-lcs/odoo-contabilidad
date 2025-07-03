{
    'name': 'Daily sales lock date',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom module to update analytic lines',
    'license': 'LGPL-3',
    'author': 'Newcom LCS',
    'description': 'Add a input for daily sales lock date',
    'depends': ['account', 'account_accountant'],
    'data': [
        'wizard/account_change_lock_date.xml',
    ],
    'installable': True,
    'application': False,
}
