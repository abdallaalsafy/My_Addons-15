
"""
XML-RPC Read Operation Module
=============================

This module provides functionality to read records from Odoo using XML-RPC protocol.
It demonstrates how to perform search and read operations on Odoo models from
external applications.

The module specifically focuses on reading partner records but can be adapted
for any Odoo model and can be customized with different domains and fields.
"""


def read_partner_record(operation, password, db, user_id):
    """
    Read partner records using XML-RPC search_read operation
    
    This function demonstrates how to retrieve partner records from Odoo
    through the XML-RPC protocol using the search_read method, which combines
    search and read operations in a single call.
    
    Args:
        operation: XML-RPC operation proxy object for executing commands
        password (str): User password for authentication
        db (str): Database name
        user_id (int): Authenticated user ID
        
    Returns:
        list/bool: List of partner records with specified fields, or False if operation failed
        
    Example:
        >>> partners = read_partner_record(operation, password, db, user_id)
        >>> if partners:
        ...     for partner in partners:
        ...         print(f"Partner: {partner['name']}")
        
    Note:
        - Empty domain [] means no filters - returns all records
        - Fields list specifies which fields to retrieve for performance
        - In production, consider adding pagination for large datasets
    """
    # Define search domain (empty = no filters, returns all records)
    domain = []
    
    # Specify which fields to retrieve (reduces data transfer)
    fields = ['id', 'name', 'email', 'phone']

    try:
        # [domain] --> this is parama of basic parametres must be list
        # {} --> this is parama of optional parametres must be dict
        # Execute search_read operation via XML-RPC
        # search_read combines search and read in one efficient call
        # execute -->> old way
        # execute_kw -->> new way
        partner_ids = operation.execute_kw(db, user_id, password, 'res.partner', 'search', [domain],{})
        partner_count = operation.execute_kw(db, user_id, password, 'res.partner', 'search_count', [domain],{})
        partner_rcrdset = operation.execute_kw(db, user_id, password, 'res.partner', 'search_read', [domain],{'fields':['name','email']})
        partner_lst = operation.execute_kw(db, user_id, password, 'res.partner', 'read', [partner_ids],{'fields':['name','email']})

        # Display retrieved data
        if partner_lst:
            print(f"Successfully read partner data:")
            print(f"  partner_rcrdset: {partner_rcrdset}")
            print(f"  partner_lst: {partner_lst}")
            print(f"  partner_count: {partner_count}")
            for partner in partner_lst:
                print(f"  partner : {partner}")
                print("--------------------------------")
        else:
            print("Failed to read partner data")

        return partner_lst
    except Exception as e:
        # Handle any exceptions during the read process
        print(f"Error searching partner records: {e}")
        return False