{
    'name': 'Analytic Required Purchase',
    'version': '16.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Make analytic distribution required for specific products',
    'description': """
        Makes analytic distribution required for service products with expense account
    """,
    'author': 'Newcom LCS',
    'website': 'https://www.newcom-lcs.com',
    'depends': ['purchase'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 