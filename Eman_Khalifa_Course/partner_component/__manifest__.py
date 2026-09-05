# -*- coding: utf-8 -*-
{
    'name': "Partner Component",
    'summary': """
        Partner Component
        """,
    'description': """
        Partner Component
    """,
    'author': "abdalla alsafy",
    'website': "http://www.facebook.com/abdalla6alsafy",
    'category': 'Sales',
    'version': '15.0.0.0',
    'depends': ['sale'],
    'data': [
            'views/sale_order.xml',
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_qweb': [
            'partner_component/static/src/xml/partner_component.xml',
        ],
        'web.assets_backend':[
            'partner_component/static/src/js/partner_component.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
