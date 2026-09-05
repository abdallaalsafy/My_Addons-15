# -*- coding: utf-8 -*-
{
    'name': "POS Auth Discount",
    'summary': """
        POS Auth Discount
        """,
    'description': """
        POS Auth Discount
    """,
    'author': "abdalla alsafy",
    'website': "http://www.facebook.com/abdalla6alsafy",
    'category': 'Sales',
    'version': '15.0.0.0',
    'depends': ['pos_discount'],
    'data': [
            'views/pos_config.xml',
    ],
    'demo': [
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_auth_discount/static/src/js/pos_discount_password.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
