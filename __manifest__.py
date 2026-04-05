{
    'name': 'Office Client Cards',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Manage client cards, invoices, payments, and debts.',
    'description': """
        This module allows the office to manage clients, track their invoices and payments,
        and calculate their total debts. It supports year-round discounts, per-invoice discounts,
        and no-discount clients.
    """,
    'author': 'Your Company',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/office_client_views.xml',
        'views/office_product_views.xml',
        'views/client_transaction_views.xml',
        'views/office_expense_views.xml',
        'views/factory_account_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
