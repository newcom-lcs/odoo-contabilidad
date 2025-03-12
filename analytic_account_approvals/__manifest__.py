{
    'name': 'Analytic Account Approvals',
    'version': '16.0.1.0.1',
    'category': 'Approvals',
    'summary': 'Add analytic account to approval request product lines',
    'description': """
        This module allows you to add analytic accounts to approval request product lines.
        The selected analytic accounts will be used when generating purchase orders.
    """,
    'author': 'Newcom',
    'depends': [
        'approvals',
        'analytic',
        'purchase',
        'purchase_requisition',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_product_line_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'post_update_hook': 'post_update_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 