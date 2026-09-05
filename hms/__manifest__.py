# -*- coding: utf-8 -*-
{
    'name': "Hospitals Management System",
    'summary': """
        Hospitals Management System
        """,
    'description': """
        Hospitals Management System
    """,
    'author': "abdalla alsafy",
    'website': "http://www.facebook.com/abdalla6alsafy",
    'category': 'Sales',
    'version': '15.0.0.0',
    'depends': ['base', 'crm'],
    'data': [
            'security/groups_rules.xml',
            'security/ir.model.access.csv',
            'views/patient.xml',
            'views/department.xml',
            'views/doctor.xml',
            'views/partners.xml',
            'report/patient_report.xml',
            'views/menus.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
