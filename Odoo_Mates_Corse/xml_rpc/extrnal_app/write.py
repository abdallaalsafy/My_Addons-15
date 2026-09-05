
"""
XML-RPC Write Operation Module
==============================

This module provides functionality to update records in Odoo using XML-RPC protocol.
It demonstrates how to perform write (update) operations on Odoo models from
external applications.

The module specifically focuses on updating partner records but can be adapted
for any Odoo model and can be customized with different update data.
"""


def write_partner_record(operation, password, db, user_id):
    """
    Update an existing partner record using XML-RPC write operation
    
    This function demonstrates how to update an existing partner record in Odoo
    through the XML-RPC protocol. It prepares update data and sends it to
    the Odoo instance for record modification.
    
    Args:
        operation: XML-RPC operation proxy object for executing commands
        password (str): User password for authentication
        db (str): Database name
        user_id (int): Authenticated user ID
        
    Returns:
        bool: True if the update was successful, False if it failed
        
    Example:
        >>> success = write_partner_record(operation, password, db, user_id)
        >>> if success:
        ...     print("Partner updated successfully")
        
    Note:
        - The partner ID is hardcoded for demonstration purposes
        - In production applications, the ID and data should be passed as parameters
        - The write operation returns True on success, False on failure
        - Always verify the record exists before attempting to update
    """
    # Define the data to update for the partner record
    partner_data = {
        'name': 'Write Partner4',           # Updated partner name
        'email': 'test@example.com',        # Updated email address
        'phone': '01234567890',             # Updated phone number
        'is_company': True                 # Mark as company
    }
    
    # Specify the ID of the partner record to update
    partner_id = 7

    try:
        # Execute the write operation via XML-RPC
        # Note: The ID must be passed as a list [partner_id]
        success = operation.execute_kw(db, user_id, password, 'res.partner', 'write', [[partner_id], partner_data])

        # Check if the operation was successful
        if success:
            print(f"Successfully updated partner with ID: {partner_id}")
        else:
            print(f"Failed to update partner with ID: {partner_id}")

        return success
    except Exception as e:
        # Handle any exceptions during the update process
        print(f"Error updating partner record: {e}")
        return False