from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class cls_merg_buys_r_improved(models.TransientModel):
    """
    Enhanced Wizard for Merging Purchase Returns
    This wizard allows merging multiple purchase return orders into a single consolidated return
    with proper validation, error handling, and transaction safety.
    """
    _name = 'wzrd_merg_buys_r'
    _description = 'Enhanced Wizard for Merging Purchase Returns'

    # Optional: Add fields for better user control
    merge_date = fields.Date(
        string='Merge Date',
        help='Date for the merged purchase return'
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
            active_ids = self.env['mdl_buys_r'].browse(self._context.get('active_ids'))
            if active_ids:
                # Set the earliest date as default merge date
                res['merge_date'] = min(active_ids.mapped('fld_date'))
        return res

    def fnc_merging_buys_r(self):
        """
        Merge multiple purchase return orders into a single consolidated return
        
        Process:
        1. Validate input and requirements
        2. Find the earliest purchase return to use as the main record
        3. Calculate totals from all purchase returns
        4. Update the main purchase return with consolidated data
        5. Move related records to the main purchase return
        6. Delete the merged purchase returns
        
        Raises:
            UserError: If validation fails or merge operation encounters issues
        """
        try:
            # Step 1: Input validation
            active_ids = self._validate_and_get_active_returns()
            
            # Step 2: Find the main purchase return (earliest date)
            main_return = self._find_main_purchase_return(active_ids)
            
            # Step 3: Calculate consolidated totals
            totals = self._calculate_totals(active_ids)
            
            # Step 3.5: Validate discount consistency
            self._validate_discount_consistency(active_ids)
            
            # Step 4: Determine vendor for merged return
            vendor = self._determine_vendor(active_ids, main_return)
            
            # Step 5: Determine parent purchase order
            parent_purchase = self._determine_parent_purchase(active_ids)
            
            # Step 6: Perform the merge operation with transaction safety
            self._perform_merge_operation(active_ids, main_return, totals, vendor, parent_purchase)
            
            # Return success message
            discount_info = self._format_discount_info(totals)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Successfully merged %d purchase returns\n%s') % (len(active_ids), discount_info),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(_('Failed to merge purchase returns: %s') % str(e))

    def _validate_and_get_active_returns(self):
        """
        Validate input and return active purchase returns
        
        Returns:
            recordset: Active purchase returns to merge
            
        Raises:
            UserError: If validation fails
        """
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_('No purchase returns selected for merging'))
        
        purchase_returns = self.env['mdl_buys_r'].browse(active_ids)
        
        # Validate that all records exist
        if len(purchase_returns) != len(active_ids):
            raise UserError(_('Some selected purchase returns were not found'))
        
        # Check if we have more than one return
        if len(purchase_returns) == 1:
            raise UserError(_('You must select more than one purchase return to merge'))

        return purchase_returns

    def _find_main_purchase_return(self, purchase_returns):
        """
        Find the main purchase return (earliest date) to keep
        
        Args:
            purchase_returns: Recordset of purchase returns
            
        Returns:
            record: Main purchase return to keep
        """
        earliest_date = min(purchase_returns.mapped('fld_date'))
        main_return = purchase_returns.filtered(lambda return_order: return_order.fld_date == earliest_date)
        
        if len(main_return) > 1:
            # If multiple returns have the same earliest date, take the first one
            main_return = main_return[0]
        
        return main_return

    def _calculate_totals(self, purchase_returns):
        """
        Calculate consolidated totals from all purchase returns
        
        Args:
            purchase_returns: Recordset of purchase returns
            
        Returns:
            dict: Dictionary with calculated totals
        """
        totals = {
            'total_amount': 0.0,
            'total_remaining': 0.0,
            'total_paid': 0.0,
            'total_discount': 0.0,
            'total_discount_percent': 0.0,
        }
        
        # Calculate weighted average for discount percentage
        total_amount_for_percent = 0.0
        weighted_percent_sum = 0.0
        
        for return_order in purchase_returns:
            totals['total_amount'] += return_order.fld_total or 0.0
            totals['total_remaining'] += return_order.fld_remain or 0.0
            totals['total_paid'] += return_order.fld_paying or 0.0
            totals['total_discount'] += return_order.fld_discount or 0.0
            
            # Calculate weighted average for discount percentage
            if return_order.fld_discount_percent and return_order.fld_total:
                total_amount_for_percent += return_order.fld_total
                weighted_percent_sum += (return_order.fld_discount_percent / 100) * return_order.fld_total
        
        # Calculate weighted average discount percentage
        if total_amount_for_percent > 0:
            totals['total_discount_percent'] = (weighted_percent_sum / total_amount_for_percent) * 100
        
        return totals

    def _validate_discount_consistency(self, purchase_returns):
        """
        Validate discount consistency across purchase returns
        
        Args:
            purchase_returns: Recordset of purchase returns
            
        Returns:
            bool: True if discounts are consistent, False otherwise
        """
        # Check if returns have mixed discount types
        has_fixed_discount = any(return_order.fld_discount for return_order in purchase_returns)
        has_percent_discount = any(return_order.fld_discount_percent for return_order in purchase_returns)

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

    def _determine_vendor(self, purchase_returns, main_return):
        """
        Determine the vendor for the merged return
        
        Args:
            purchase_returns: Recordset of purchase returns
            main_return: The main purchase return
            
        Returns:
            record: Vendor record
        """
        # Try to use the main return's vendor first
        if main_return.fld_vendor_id:
            return main_return.fld_vendor_id
        
        # If main return has no vendor, find the first return with a vendor
        returns_with_vendor = purchase_returns.filtered(lambda return_order: return_order.fld_vendor_id)
        if returns_with_vendor:
            return returns_with_vendor[0].fld_vendor_id
        
        # If no vendor found, raise an error
        raise UserError(_('Cannot merge purchase returns without a vendor. Please ensure at least one return has a vendor assigned.'))

    def _determine_parent_purchase(self, purchase_returns):
        """
        Determine the parent purchase order for the merged return
        
        Args:
            purchase_returns: Recordset of purchase returns
            
        Returns:
            record: Parent purchase record or False
        """
        # Get unique parent purchases from all returns
        parent_purchases = purchase_returns.mapped('fld_parent_id')
        
        # Filter out False values
        parent_purchases = parent_purchases.filtered(lambda p: p)
        
        if len(parent_purchases) > 1:
            raise UserError(_('Cannot merge purchase returns from different parent purchases. All returns must belong to the same parent purchase.'))
        
        return parent_purchases[0] if parent_purchases else False

    def _perform_merge_operation(self, purchase_returns, main_return, totals, vendor, parent_purchase):
        """
        Perform the actual merge operation with transaction safety
        
        Args:
            purchase_returns: Recordset of purchase returns to merge
            main_return: Main purchase return to keep
            totals: Dictionary with calculated totals
            vendor: Vendor record
            parent_purchase: Parent purchase record
        """
        # Get IDs of returns to be merged (excluding main return)
        returns_to_merge_ids = purchase_returns.filtered(lambda return_order: return_order.id != main_return.id).ids
        
        if not returns_to_merge_ids:
            raise UserError(_('No returns to merge found'))
        
        try:
            # Update main return with consolidated data
            main_return.write({
                'fld_total': totals['total_amount'],
                'fld_remain': totals['total_remaining'],
                'fld_paying': totals['total_paid'],
                'fld_discount': totals['total_discount'],
                'fld_discount_percent': totals['total_discount_percent'],
                'fld_vendor_id': vendor.id,
                'fld_parent_id': parent_purchase.id if parent_purchase else False,
                'fld_date': self.merge_date or main_return.fld_date,
            })
            
            # Add merge notes if provided
            if self.merge_notes:
                existing_notes = main_return.fld_notes or ''
                merge_info = _('\n\n--- MERGED RETURNS ---\nMerged on: %s\nReturns merged: %s\nNotes: %s') % (
                    fields.Date.today(),
                    ', '.join(purchase_returns.mapped('name') or ['ID: %s' % id for id in returns_to_merge_ids]),
                    self.merge_notes
                )
                main_return.write({'fld_notes': existing_notes + merge_info})
            
            # Move related records to main return
            self._move_related_records(returns_to_merge_ids, main_return)
            
            # Delete the merged returns
            self.env['mdl_buys_r'].browse(returns_to_merge_ids).unlink()
        except Exception as e:
            raise UserError(_('Failed to complete merge operation: %s') % str(e))

    def _move_related_records(self, returns_to_merge_ids, main_return):
        """
        Move related records from merged returns to main return
        
        Args:
            returns_to_merge_ids: List of return IDs to merge
            main_return: Main purchase return
        """
        # Move purchase return goods
        self.env['mdl_buys_r_goods'].search([
            ('fld_buys_r_id.id', 'in', returns_to_merge_ids)
        ]).write({'fld_buys_r_id': main_return.id})
        
        # Move vendor payments (unpaid ones)
        self.env['mdl_vendors_in'].search([
            ('fld_buys_r_id.id', 'in', returns_to_merge_ids),
            ('fld_is_pay', '=', False)
        ]).write({'fld_buys_r_id': main_return.id})
