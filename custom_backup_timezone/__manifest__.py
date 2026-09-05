# -*- coding: utf-8 -*-
{
    'name': 'Custom Backup Timezone',
    'version': '15.0.1.0.0',
    'summary': 'Customize backup filename with user timezone',
    'description': """
        Custom Backup Timezone Module
        ============================
        
        This module customizes the backup filename to use the user's timezone
        instead of UTC time for better user experience.
        
        Features:
        - Uses user's timezone for backup filename timestamp
        - Maintains original backup functionality
        - Easy to install and configure
    """,
    'author': 'Custom Developer',
    'website': 'https://www.example.com',
    'category': 'Technical',
    'depends': ['base', 'web'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
