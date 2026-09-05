# -*- coding: utf-8 -*-
{
    'name': "Pos Button In Payment",
    'summary': """
        Pos Button In Payment
        """,
    'description': """
        Pos Button In Payment
    """,
    'author': "abdalla alsafy",
    'website': "http://www.facebook.com/abdalla6alsafy",
    'category': 'Sales',
    'version': '15.0.0.0',
    'depends': ['point_of_sale'],
    'data': [
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_qweb': [
            'pos_button_in_payment/static/src/xml/pos_button_in_payment.xml',
        ],
        'web.assets_backend':[
            'pos_button_in_payment/static/src/js/pos_button_in_payment.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
