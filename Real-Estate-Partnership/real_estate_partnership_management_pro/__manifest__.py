# -*- coding: utf-8 -*-
{
    'name': 'Real Estate Partnership Management Pro',
    'version': '15.0.2.0.0',
    'category': 'Real Estate',
    'summary': 'Comprehensive real estate partnership management system',
    'description': """
Real Estate Partnership Management Module
========================================

This module provides a complete solution for managing real estate partnerships:

Features:

    """,
    'author': 'Abdallaalsafy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web','mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/expense_category_data.xml',
        'data/sequence_data.xml',

        'wizards/views/payment_filter_wizard_views.xml',
        'wizards/views/partner_unified_ledger_views.xml',
        'wizards/views/property_payment_receipts_wizard_views.xml',
        'wizards/views/company_financial_summary_views.xml',

        'views/partner_views.xml',
        'views/property_views.xml',
        'views/deal_views.xml',
        'views/investment_views.xml',
        'views/investment_payment_views.xml',
        'views/expense_views.xml',
        'views/expense_category_views.xml',
        'views/sale_lines_views.xml',
        'views/transaction_views.xml',
        'views/company_settings_views.xml',
        'views/payment_installment_views.xml',

        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'sequence': 100,
}
