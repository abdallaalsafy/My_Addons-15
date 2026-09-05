
"""
XML-RPC Create Operation Module
===============================

This module provides functionality to create records in Odoo using XML-RPC protocol.
It demonstrates how to perform create operations on Odoo models from external
applications.

The module specifically focuses on creating partner records but can be adapted
for any Odoo model.
"""


def create_partner_record(operation, password, db, user_id):
    """
    Create a new partner record using XML-RPC
    
    This function demonstrates how to create a new partner record in Odoo
    through the XML-RPC protocol. It prepares partner data and sends it to
    the Odoo instance for record creation.
    
    Args:
        operation: XML-RPC operation proxy object for executing commands
        password (str): User password for authentication
        db (str): Database name
        user_id (int): Authenticated user ID
        
    Returns:
        int/bool: The ID of the newly created partner record, or False if creation failed
        
    Example:
        >>> record_id = create_partner_record(operation, password, db, user_id)
        >>> if record_id:
        ...     print(f"Partner created with ID: {record_id}")
        
    Note:
        The partner data is hardcoded for demonstration purposes. In production
        applications, this data should be passed as parameters or obtained
        from user input/configuration files.
    """
    # Define partner data for the new record
    partner_data = {
        'name': 'abdallaalsafy1',           # Partner name (required field)
        'email': 'test@example.com',       # Email address
        'phone': '01234567890',           # Phone number
        'is_company': True                # Mark as company rather than individual
    }
    
    try:
        # Execute the create operation via XML-RPC
        record_id = operation.execute_kw(db, user_id, password, 'res.partner', 'create', [partner_data])

        # Check if the operation was successful
        if record_id:
            print(f"Successfully created partner with ID: {record_id}")
        else:
            print("Failed to create partner")

        return record_id
    except Exception as e:
        # Handle any exceptions during the creation process
        print(f"Error creating partner record: {e}")
        return False