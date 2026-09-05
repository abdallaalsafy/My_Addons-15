# -*- coding: utf-8 -*-
{
    'name': "Warehouse Journal restriction",

    'summary': "",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Uncategorized',
    'version': '17.4',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','account'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/record_rules.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}

