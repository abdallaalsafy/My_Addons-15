# -*- coding: utf-8 -*-
{
    # Module identification
    'name': 'XML-RPC API Module',
    'version': '15.0.1.0.0',
    'description': 'Provides XML-RPC functionality for external integrations',
    'category': 'Technical',
    'summary': 'Provides XML-RPC functionality for external integrations',
    
    # Author and licensing information
    'author': 'Odoo Mates Course',
    'website': 'https://www.odoomates.com',
    'license': 'LGPL-3',
    
    # Required dependencies for the module to function
    'depends': [
        'base',        # Core Odoo functionality
        'contacts',    # Partner/contact management
    ],
    
    # Data files to be loaded during module installation
    # Currently commented out as no security or view configurations are needed
    'data': [
    ],
    
    # Demo data for testing and demonstration purposes
    'demo': [],
    
    # Installation and behavior settings
    'installable': True,     # Module can be installed
    'auto_install': False,   # Module won't auto-install with dependencies
    'application': False,    # Not a standalone application
    'sequence': 100,         # Loading order in module list
    'images': [],            # Screenshots for app store
}
