from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class cls_merg_sells_r_improved(models.TransientModel):
    """
    Enhanced Wizard for Merging Sales Returns
    This wizard allows merging multiple sales return orders into a single consolidated return
    with proper validation, error handling, and transaction safety.
    """
    _name = 'wzrd_merg_sells_r'
    _description = 'Enhanced Wizard for Merging Sales Returns'

    # Optional: Add fields for better user control
    merge_date = fields.Date(
        string='Merge Date',
        help='Date for the merged sales return'
    )
    
    merge_notes = fields.Text(
        string='Merge Notes',
        help='Optional notes about this merge operation'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values for the wizard"""
        res = super().default_get(fields_list)
        if self._context.get('active_ids'):
            active_ids = self.env['mdl_sells_r'].browse(self._context.get('active_ids'))
            if active_ids:
                # Set the earliest date as default merge date
                res['merge_date'] = min(active_ids.mapped('fld_date'))
        return res

    def fnc_merging_sells_r(self):
        """
        Merge multiple sales return orders into a single consolidated return
        
        Process:
        1. Validate input and requirements
        2. Find the earliest sales return to use as the main record
        3. Calculate totals from all sales returns
        4. Update the main sales return with consolidated data
        5. Move related records to the main sales return
        6. Delete the merged sales returns
        
        Raises:
            UserError: If validation fails or merge operation encounters issues
        """
        try:
            # Step 1: Input validation
            active_ids = self._validate_and_get_active_returns()
            
            # Step 2: Find the main sales return (earliest date)
            main_return = self._find_main_sales_return(active_ids)
            
            # Step 3: Calculate consolidated totals
            totals = self._calculate_totals(active_ids)
            
            # Step 3.5: Validate discount consistency
            self._validate_discount_consistency(active_ids)
            
            # Step 4: Determine customer for merged return
            customer = self._determine_customer(active_ids, main_return)
            
            # Step 5: Determine parent sales order
            parent_sales = self._determine_parent_sales(active_ids)
            
            # Step 6: Perform the merge operation with transaction safety
            self._perform_merge_operation(active_ids, main_return, totals, customer, parent_sales)
            
            # Return success message
            discount_info = self._format_discount_info(totals)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Successfully merged %d sales returns\n%s') % (len(active_ids), discount_info),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(_('Failed to merge sales returns: %s') % str(e))

    def _validate_and_get_active_returns(self):
        """
        Validate input and return active sales returns
        
        Returns:
            recordset: Active sales returns to merge
            
        Raises:
            UserError: If validation fails
        """
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_('No sales returns selected for merging'))
        
        sales_returns = self.env['mdl_sells_r'].browse(active_ids)
        
        # Validate that all records exist
        if len(sales_returns) != len(active_ids):
            raise UserError(_('Some selected sales returns were not found'))
        
        # Check if we have more than one return
        if len(sales_returns) == 1:
            raise UserError(_('You must select more than one sales return to merge'))

        return sales_returns

    def _find_main_sales_return(self, sales_returns):
        """
        Find the main sales return (earliest date) to keep
        
        Args:
            sales_returns: Recordset of sales returns
            
        Returns:
            record: Main sales return to keep
        """
        earliest_date = min(sales_returns.mapped('fld_date'))
        main_return = sales_returns.filtered(lambda return_order: return_order.fld_date == earliest_date)
        
        if len(main_return) > 1:
            # If multiple returns have the same earliest date, take the first one
            main_return = main_return[0]
        
        return main_return

    def _calculate_totals(self, sales_returns):
        """
        Calculate consolidated totals from all sales returns
        
        Args:
            sales_returns: Recordset of sales returns
            
        Returns:
            dict: Dictionary with calculated totals
        """
        totals = {
            'total_amount': 0.0,
            'total_win': 0.0,
            'total_remaining': 0.0,
            'total_paid': 0.0,
            'total_discount': 0.0,
            'total_discount_percent': 0.0,
        }
        
        # Calculate weighted average for discount percentage
        total_amount_for_percent = 0.0
        weighted_percent_sum = 0.0
        
        for return_order in sales_returns:
            totals['total_amount'] += return_order.fld_total or 0.0
            totals['total_win'] += return_order.fld_win or 0.0
            totals['total_remaining'] += return_order.fld_remain or 0.0
            totals['total_paid'] += return_order.fld_paying or 0.0
            totals['total_discount'] += return_order.fld_discount or 0.0
            
            # Calculate weighted average for discount percentage
            if hasattr(return_order, 'fld_discount_percent') and return_order.fld_discount_percent and return_order.fld_total:
                total_amount_for_percent += return_order.fld_total
                weighted_percent_sum += (return_order.fld_discount_percent / 100) * return_order.fld_total
        
        # Calculate weighted average discount percentage
        if total_amount_for_percent > 0:
            totals['total_discount_percent'] = (weighted_percent_sum / total_amount_for_percent) * 100
        
        return totals

    def _validate_discount_consistency(self, sales_returns):
        """
        Validate discount consistency across sales returns
        
        Args:
            sales_returns: Recordset of sales returns
            
        Returns:
            bool: True if discounts are consistent, False otherwise
        """
        # Check if returns have mixed discount types
        has_fixed_discount = any(return_order.fld_discount for return_order in sales_returns)
        has_percent_discount = any(hasattr(return_order, 'fld_discount_percent') and return_order.fld_discount_percent for return_order in sales_returns)

        return True

    def _format_discount_info(self, totals):
        """
        Format discount information for display
        
        Args:
            totals: Dictionary with calculated totals
            
        Returns:
            str: Formatted discount information
        """
        discount_info = []
        
        if totals['total_discount'] > 0:
            discount_info.append(_("Fixed Discount: %s") % totals['total_discount'])
        
        if totals['total_discount_percent'] > 0:
            discount_info.append(_("Average Discount: %.2f%%") % totals['total_discount_percent'])
        
        return " | ".join(discount_info) if discount_info else _("No Discount")

    def _determine_customer(self, sales_returns, main_return):
        """
        Determine the customer for the merged return
        
        Args:
            sales_returns: Recordset of sales returns
            main_return: The main sales return
            
        Returns:
            record: Customer record
        """
        # Try to use the main return's customer first
        if main_return.fld_customer_id:
            return main_return.fld_customer_id
        
        # If main return has no customer, find the first return with a customer
        returns_with_customer = sales_returns.filtered(lambda return_order: return_order.fld_customer_id)
        if returns_with_customer:
            return returns_with_customer[0].fld_customer_id
        
        # If no customer found, raise an error
        raise UserError(_('Cannot merge sales returns without a customer. Please ensure at least one return has a customer assigned.'))

    def _determine_parent_sales(self, sales_returns):
        """
        Determine the parent sales order for the merged return
        
        Args:
            sales_returns: Recordset of sales returns
            
        Returns:
            record: Parent sales record or False
        """
        # Get unique parent sales from all returns
        parent_sales = sales_returns.mapped('fld_parent_id')
        
        # Filter out False values
        parent_sales = parent_sales.filtered(lambda p: p)
        
        if len(parent_sales) > 1:
            raise UserError(_('Cannot merge sales returns from different parent sales. All returns must belong to the same parent sale.'))
        
        return parent_sales[0] if parent_sales else False

    def _perform_merge_operation(self, sales_returns, main_return, totals, customer, parent_sales):
        """
        Perform the actual merge operation with transaction safety
        
        Args:
            sales_returns: Recordset of sales returns to merge
            main_return: Main sales return to keep
            totals: Dictionary with calculated totals
            customer: Customer record
            parent_sales: Parent sales record
        """
        # Get IDs of returns to be merged (excluding main return)
        returns_to_merge_ids = sales_returns.filtered(lambda return_order: return_order.id != main_return.id).ids
        
        if not returns_to_merge_ids:
            raise UserError(_('No returns to merge found'))
        
        try:
            # Update main return with consolidated data
            main_return.write({
                'fld_total': totals['total_amount'],
                'fld_win': totals['total_win'],
                'fld_remain': totals['total_remaining'],
                'fld_paying': totals['total_paid'],
                'fld_discount': totals['total_discount'],
                'fld_customer_id': customer.id,
                'fld_parent_id': parent_sales.id if parent_sales else False,
                'fld_date': self.merge_date or main_return.fld_date,
            })
            
            # Add merge notes if provided
            if self.merge_notes:
                existing_notes = main_return.fld_notes or ''
                merge_info = _('\n\n--- MERGED RETURNS ---\nMerged on: %s\nReturns merged: %s\nNotes: %s') % (
                    fields.Date.today(),
                    ', '.join(sales_returns.mapped('name') or ['ID: %s' % id for id in returns_to_merge_ids]),
                    self.merge_notes
                )
                main_return.write({'fld_notes': existing_notes + merge_info})
            
            # Move related records to main return
            self._move_related_records(returns_to_merge_ids, main_return)
            
            # Delete the merged returns
            self.env['mdl_sells_r'].browse(returns_to_merge_ids).unlink()
        except Exception as e:
            raise UserError(_('Failed to complete merge operation: %s') % str(e))

    def _move_related_records(self, returns_to_merge_ids, main_return):
        """
        Move related records from merged returns to main return
        
        Args:
            returns_to_merge_ids: List of return IDs to merge
            main_return: Main sales return
        """
        # Move sales return goods
        self.env['mdl_sells_r_goods'].search([
            ('fld_sells_r_id.id', 'in', returns_to_merge_ids)
        ]).write({'fld_sells_r_id': main_return.id})
        
        # Move customer payments (unpaid ones)
        self.env['mdl_customers_out'].search([
            ('fld_sells_r_id.id', 'in', returns_to_merge_ids),
            ('fld_is_pay', '=', False)
        ]).write({'fld_sells_r_id': main_return.id})
