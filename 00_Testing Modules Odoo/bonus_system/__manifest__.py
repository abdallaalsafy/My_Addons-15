{
    'name': 'Bonus System',
    'summary': 'Bonus System',
    'author': "Eslam  Moh",
    'company': 'elfath(Thebes)',
    'version': '15.0.0.1.0',
    'category': 'account',
    'license': 'AGPL-3',
    'sequence': 1,
    'depends': [
        'base',
        'product',
        'account',
        'hr',
        'hr_contract',
        # 'hr_payroll'
    ],
    'data': [
        'views/product_product_view.xml',
        'views/invoice_view.xml',
        'views/hr_contract_view.xml',
    ],
    'demo': [
        # 'demo/',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
