# my_custom_module/__manifest__.py
{
    'name': 'Centro de Costeo (Empleados)',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Set default analytic account and payment methods for employee expenses',
    'description': """
        This module allows setting a default analytic account and default payment methods
        for employees when they register expenses.
    """,
    'license': 'LGPL-3',
    'author': 'Newcom LCS',
    'depends': ['hr', 'hr_expense', 'account'],
    'data': [
        'views/hr_employee_views.xml',
        'views/hr_expense_views.xml',
    ],
    'installable': True,
    'application': False,
}
