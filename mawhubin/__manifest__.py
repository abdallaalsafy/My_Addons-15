# -*- coding: utf-8 -*-
{
    'name': "mawhubin",

    'summary': """
        """,

    'description': """
        
    """,

    'author': "Mohammed Basem Rabei",
    'website': "https://www.facebook.com/profile.php?id=100079188224394&mibextid=ZbWKwL",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly


    # always loaded
    'data': [
        'data/mawhubin2.csv',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/views2.xml',
        # 'views/templates.xml',
    ],
    'qweb': [
        "static/src/xml/zxczxc.xml",
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

}
