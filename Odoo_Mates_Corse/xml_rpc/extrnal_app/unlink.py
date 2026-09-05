
"""
XML-RPC Unlink Operation Module
================================

This module provides functionality to delete records in Odoo using XML-RPC protocol.
It demonstrates how to perform unlink (delete) operations on Odoo models from
external applications.

The module specifically focuses on deleting partner records but can be adapted
for any Odoo model. Use with caution as delete operations are irreversible.
"""


def unlink_partner_record(operation, password, db, user_id):
    """
    Delete a partner record using XML-RPC unlink operation
    
    This function demonstrates how to delete an existing partner record in Odoo
    through the XML-RPC protocol. The unlink operation permanently removes
    the record from the database.
    
    Args:
        operation: XML-RPC operation proxy object for executing commands
        password (str): User password for authentication
        db (str): Database name
        user_id (int): Authenticated user ID
        
    Returns:
        bool: True if the deletion was successful, False if it failed
        
    Example:
        >>> success = unlink_partner_record(operation, password, db, user_id)
        >>> if success:
        ...     print("Partner deleted successfully")
        
    Warning:
        - The unlink operation is permanent and cannot be undone
        - Always verify the record ID before deletion
        - Consider using archive (active=False) instead of delete when possible
        - The partner ID is hardcoded for demonstration purposes
        
    Note:
        - In production applications, the ID should be passed as a parameter
        - The unlink operation returns True on success, False on failure
        - Ensure proper permissions are set for delete operations
    """
    # Specify the ID of the partner record to delete
    partner_id = 8

    try:
        # Execute the unlink operation via XML-RPC
        # Note: The ID must be passed as a list [partner_id]
        success = operation.execute_kw(db, user_id, password, 'res.partner', 'unlink', [[partner_id]])

        # Check if the operation was successful
        if success:
            print(f"Successfully deleted partner with ID: {partner_id}")
        else:
            print(f"Failed to delete partner with ID: {partner_id}")

        return success
    except Exception as e:
        # Handle any exceptions during the deletion process
        print(f"Error deleting partner records: {e}")
        return False