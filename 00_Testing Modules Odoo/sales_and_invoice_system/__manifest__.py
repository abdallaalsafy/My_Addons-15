{
    'name': 'Sales & Invoice System',
    'summary': 'Sales & Invoice System',
    'author': "Eslam Moh",
    'company': 'Elfath(Thebes)',
    'version': '15.0.0.1.0',
    'category': 'Sales',
    'license': 'AGPL-3',
    'sequence': 1,
    'depends': [
        'base',
        'account',
        'sale',
        'contacts',
        'stock',
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_order_view.xml',
        'views/invoice_view.xml',
        'views/region_view.xml',
        'views/installement_line_view.xml',
       'report/installement_report_template_view.xml',
    ],
    'demo': [
        # 'demo/',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
