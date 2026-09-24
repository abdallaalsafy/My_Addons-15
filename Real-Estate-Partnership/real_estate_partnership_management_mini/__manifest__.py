# -*- coding: utf-8 -*-
{
    'name': 'Real Estate Partnership Management Mini',
    'version': '15.0.2.0.0',
    'category': 'Real Estate',
    'summary': 'Manage real estate partnerships, investments, payments, expenses, and reports.',
    'description': """
Real Estate Partnership Management Mini
=====================================

This module helps manage:
- partners and contact records
- properties and investments
- partnership records and payments
- expense categories and expenses
- installment payments and financial reports
- summary and cash flow reports
""",
    'author': 'Abdallaalsafy',
    'website': 'https://github.com/abdallaalsafy',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/expense_category_data.xml',
        'data/sequence_data.xml',

        'wizards/views/payment_filter_wizard_views.xml',
        'wizards/views/partner_unified_ledger_views.xml',
        'wizards/views/cash_flow_into_cash_box_views.xml',
        'wizards/views/property_payment_receipts_wizard_views.xml',
        'wizards/views/company_financial_summary_views.xml',

        'views/res_partner_views.xml',
        'views/property_views.xml',
        'views/investment_views.xml',
        'views/partnership_views.xml',
        'views/partnership_payment_views.xml',
        'views/expense_views.xml',
        'views/expense_category_views.xml',
        'views/sale_lines_views.xml',
        'views/transaction_views.xml',
        'views/company_settings_views.xml',
        'views/payment_installment_views.xml',
        'views/city_views.xml',

        'reports/property_report.xml',
        'reports/investment_report.xml',
        'reports/partnership_report.xml',
        'reports/partner_report.xml',
        'reports/partner_unified_ledger_report.xml',
        'reports/company_financial_summary_report.xml',
        'reports/cash_flow_into_cash_box_report.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'sequence': 0,
}
