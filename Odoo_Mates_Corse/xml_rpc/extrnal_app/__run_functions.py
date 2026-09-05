"""
XML-RPC Demo Execution Script
https://www.odoo.com/documentation/15.0/developer/reference/external_api.html
==============================

This script demonstrates a complete XML-RPC integration workflow with Odoo.
It executes all XML-RPC operations in sequence to show how external
applications can interact with Odoo through the XML-RPC protocol.

Operations Demonstrated:
1. Connection establishment and authentication
2. Create new partner records
3. Update existing partner records
4. Delete partner records
5. Read/search partner records
6. Call custom methods on Odoo models

This script serves as a comprehensive example and testing tool for
XML-RPC functionality provided by this module.
"""

# Import required XML-RPC library
from xmlrpc import client as xml_rpc

# Import all operation functions from the module
from connection_with_odoo import get_main_conn_data
from create import create_partner_record
from write import write_partner_record
from unlink import unlink_partner_record
from read import read_partner_record
from call_my_func import call_my_func


"""
Main execution function for XML-RPC demonstration

This function orchestrates the complete XML-RPC workflow by:
1. Establishing connection with Odoo
2. Executing all CRUD operations
3. Calling custom methods
4. Displaying results for each operation

Returns:
    None: Results are printed to the console
    
Note:
    This is a demonstration script. In production, consider:
    - Adding error handling for each operation
    - Implementing logging instead of print statements
    - Adding configuration management for connection parameters
"""
print("=== XML-RPC Demo Execution Started ===\n")

# Step 1: Establish connection with Odoo
print("Step 1: Establishing connection...")
url, user, password, db, user_id = get_main_conn_data()
operation = xml_rpc.ServerProxy(url + "/xmlrpc/2/object")
print(f"Connected to {url} as user {user} (ID: {user_id})")

# Step 2: Create a new partner record
print("Step 2: Creating partner record...")
create_result = create_partner_record(operation, password, db, user_id)
print('create_result: ', create_result)
print('--------------------------------')

# Step 3: Update an existing partner record
print("Step 3: Updating partner record...")
write_result = write_partner_record(operation, password, db, user_id)
print('write_result: ', write_result)
print('--------------------------------')

# # Step 4: Delete a partner record
print("Step 4: Deleting partner record...")
unlink_result = unlink_partner_record(operation, password, db, user_id)
print('unlink_result: ', unlink_result)
print('--------------------------------')

# Step 5: Read partner records
print("Step 5: Reading partner records...")
read_result = read_partner_record(operation, password, db, user_id)
print('read_result: ', read_result)
print('--------------------------------')
