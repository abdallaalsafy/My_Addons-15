# -*- coding: utf-8 -*-
{
    'name': "SuperMarket Installments",
    'summary': """
        SuperMarket Installments & Delivery Management for Odoo-15""",
    'description': """
        Advanced SuperMarket Module for Odoo-15
        Features: Installments System, Delivery Management (Mandoops), 
        Customer Address Management, Regions & Places Tracking
        Extension for SuperMarket Pro
    """,

    'author': "abdallaalsafy",
    'website': "http://www.facebook.com/abdalla6alsafy",
    'category': 'Sales',
    'version': '15.0.0.0',
    'depends': ['base','super_market_pro'],
    'data': [
        'security/ir.model.access.csv',

        'wizards/search_isalls.xml',
		'wizards/search_cust_addr_of_mandoops.xml',
        'wizards/search_mandoops_sells.xml',
        'wizards/search_mandoops_goods.xml',
        'wizards/received_isalls.xml',
        'wizards/convert_sells.xml',
        'wizards/update_isalls.xml',
        # 'wizards/merg_sells.xml',
        'wizards/update_goods.xml',
		'wizards/willing.xml',
        'views/mandoops.xml',
        'views/regions.xml',
        'views/places.xml',
        'views/customers.xml',
        'views/goods.xml',
        'views/sells.xml',
        'views/sells_goods.xml',
        'views/sells_r.xml',
        'views/sells_r_goods.xml',
        'views/isalls.xml',

        'querys/mandoops_sells.xml',
        'querys/mandoops_goods.xml',

        'views/menus.xml',

        'reports/reports_rtl/isalls_tahseel.xml',
		'reports/reports_rtl/goods_report.xml',
		'reports/reports_rtl/sells_report.xml',
		'reports/reports_rtl/sells_r_report.xml',
		'reports/reports_rtl/sells_goods_report.xml',
		'reports/reports_rtl/sells_r_goods_report.xml',
		'reports/reports_rtl/mandoops.xml',
        'reports/paper_format.xml',
        'reports/reports_actions.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
