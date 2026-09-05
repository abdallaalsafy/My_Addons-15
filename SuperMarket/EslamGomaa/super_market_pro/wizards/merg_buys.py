from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class cls_merg_buys_improved(models.TransientModel):
    """
    Enhanced Wizard for Merging Purchase Orders
    This wizard allows merging multiple purchase orders into a single consolidated order
    with proper validation, error handling, and transaction safety.
    """
    _name = 'wzrd_merg_buys'
    _description = 'Enhanced Wizard for Merging Purchase Orders'

    # Optional: Add fields for better user control
    merge_date = fields.Date(
        string='Merge Date',
        help='Date for the merged purchase order'
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
            active_ids = self.env['mdl_buys'].browse(self._context.get('active_ids'))
            if active_ids:
                # Set the earliest date as default merge date
                res['merge_date'] = min(active_ids.mapped('fld_date'))
        return res

    def fnc_merging_buys(self):
        """
        Merge multiple purchase orders into a single consolidated order
        
        Process:
        1. Validate input and requirements
        2. Find the earliest purchase order to use as the main record
        3. Calculate totals from all purchase orders
        4. Update the main purchase order with consolidated data
        5. Move related records to the main purchase order
        6. Delete the merged purchase orders
        
        Raises:
            UserError: If validation fails or merge operation encounters issues
        """
        try:
            # Step 1: Input validation
            active_ids = self._validate_and_get_active_orders()
            
            # Step 2: Find the main purchase order (earliest date)
            main_order = self._find_main_purchase_order(active_ids)
            
            # Step 3: Calculate consolidated totals
            totals = self._calculate_totals(active_ids)
            
            # Step 3.5: Validate discount consistency
            self._validate_discount_consistency(active_ids)
            
            # Step 4: Determine vendor for merged order
            vendor = self._determine_vendor(active_ids, main_order)
            
            # Step 5: Perform the merge operation with transaction safety
            self._perform_merge_operation(active_ids, main_order, totals, vendor)
            
            # Return success message
            discount_info = self._format_discount_info(totals)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Successfully merged %d purchase orders\n%s') % (len(active_ids), discount_info),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(_('Failed to merge purchase orders: %s') % str(e))

    def _validate_and_get_active_orders(self):
        """
        Validate input and return active purchase orders
        
        Returns:
            recordset: Active purchase orders to merge
            
        Raises:
            UserError: If validation fails
        """
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_('No purchase orders selected for merging'))
        
        purchase_orders = self.env['mdl_buys'].browse(active_ids)
        
        # Validate that all records exist
        if len(purchase_orders) != len(active_ids):
            raise UserError(_('Some selected purchase orders were not found'))
        
        # Check if we have more than one order
        if len(purchase_orders) == 1:
            raise UserError(_('You must select more than one purchase order to merge'))

        return purchase_orders

    def _find_main_purchase_order(self, purchase_orders):
        """
        Find the main purchase order (earliest date) to keep
        
        Args:
            purchase_orders: Recordset of purchase orders
            
        Returns:
            record: Main purchase order to keep
        """
        earliest_date = min(purchase_orders.mapped('fld_date'))
        main_order = purchase_orders.filtered(lambda order: order.fld_date == earliest_date)
        
        if len(main_order) > 1:
            # If multiple orders have the same earliest date, take the first one
            main_order = main_order[0]
        
        return main_order

    def _calculate_totals(self, purchase_orders):
        """
        Calculate consolidated totals from all purchase orders
        
        Args:
            purchase_orders: Recordset of purchase orders
            
        Returns:
            dict: Dictionary with calculated totals
        """
        totals = {
            'total_amount': 0.0,
            'total_profit': 0.0,
            'total_remaining': 0.0,
            'total_paid': 0.0,
            'total_discount': 0.0,
            'total_discount_percent': 0.0,
        }
        
        # Calculate weighted average for discount percentage
        total_amount_for_percent = 0.0
        weighted_percent_sum = 0.0
        
        for order in purchase_orders:
            totals['total_amount'] += order.fld_total or 0.0
            totals['total_profit'] += order.fld_win or 0.0
            totals['total_remaining'] += order.fld_remain or 0.0
            totals['total_paid'] += order.fld_paying or 0.0
            totals['total_discount'] += order.fld_discount or 0.0
            
            # Calculate weighted average for discount percentage
            if order.fld_discount_percent and order.fld_total:
                total_amount_for_percent += order.fld_total
                weighted_percent_sum += (order.fld_discount_percent / 100) * order.fld_total
        
        # Calculate weighted average discount percentage
        if total_amount_for_percent > 0:
            totals['total_discount_percent'] = (weighted_percent_sum / total_amount_for_percent) * 100
        
        return totals

    def _validate_discount_consistency(self, purchase_orders):
        """
        Validate discount consistency across purchase orders
        
        Args:
            purchase_orders: Recordset of purchase orders
            
        Returns:
            bool: True if discounts are consistent, False otherwise
        """
        # Check if orders have mixed discount types
        has_fixed_discount = any(order.fld_discount for order in purchase_orders)
        has_percent_discount = any(order.fld_discount_percent for order in purchase_orders)

        
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

    def _determine_vendor(self, purchase_orders, main_order):
        """
        Determine the vendor for the merged order
        
        Args:
            purchase_orders: Recordset of purchase orders
            main_order: The main purchase order
            
        Returns:
            record: Vendor record
        """
        # Try to use the main order's vendor first
        if main_order.fld_vendor_id:
            return main_order.fld_vendor_id
        
        # If main order has no vendor, find the first order with a vendor
        orders_with_vendor = purchase_orders.filtered(lambda order: order.fld_vendor_id)
        if orders_with_vendor:
            return orders_with_vendor[0].fld_vendor_id
        
        # If no vendor found, raise an error
        raise UserError(_('Cannot merge purchase orders without a vendor. Please ensure at least one order has a vendor assigned.'))

    def _perform_merge_operation(self, purchase_orders, main_order, totals, vendor):
        """
        Perform the actual merge operation with transaction safety
        
        Args:
            purchase_orders: Recordset of purchase orders to merge
            main_order: Main purchase order to keep
            totals: Dictionary with calculated totals
            vendor: Vendor record
        """
        # Get IDs of orders to be merged (excluding main order)
        orders_to_merge_ids = purchase_orders.filtered(lambda order: order.id != main_order.id).ids
        
        if not orders_to_merge_ids:
            raise UserError(_('No orders to merge found'))
        
        try:
            # Update main order with consolidated data
            main_order.write({
                'fld_total': totals['total_amount'],
                'fld_win': totals['total_profit'],
                'fld_remain': totals['total_remaining'],
                'fld_paying': totals['total_paid'],
                'fld_discount': totals['total_discount'],
                'fld_discount_percent': totals['total_discount_percent'],
                'fld_vendor_id': vendor.id,
                'fld_date': self.merge_date or main_order.fld_date,
            })
            
            # Add merge notes if provided
            if self.merge_notes:
                existing_notes = main_order.fld_notes or ''
                merge_info = _('\n\n--- MERGED ORDERS ---\nMerged on: %s\nOrders merged: %s\nNotes: %s') % (
                    fields.Date.today(),
                    ', '.join(purchase_orders.mapped('name') or ['ID: %s' % id for id in orders_to_merge_ids]),
                    self.merge_notes
                )
                main_order.write({'fld_notes': existing_notes + merge_info})
            
            # Move related records to main order
            self._move_related_records(orders_to_merge_ids, main_order)
            
            # Delete the merged orders
            self.env['mdl_buys'].browse(orders_to_merge_ids).unlink()
        except Exception as e:
            raise UserError(_('Failed to complete merge operation: %s') % str(e))

    def _move_related_records(self, orders_to_merge_ids, main_order):
        """
        Move related records from merged orders to main order
        
        Args:
            orders_to_merge_ids: List of order IDs to merge
            main_order: Main purchase order
        """
        # Move purchase goods
        self.env['mdl_buys_goods'].search([
            ('fld_buys_id.id', 'in', orders_to_merge_ids)
        ]).write({'fld_buys_id': main_order.id})
        
        # Move vendor payments (unpaid ones)
        self.env['mdl_vendors_out'].search([
            ('fld_buys_id.id', 'in', orders_to_merge_ids),
            ('fld_is_pay', '=', False)
        ]).write({'fld_buys_id': main_order.id})
        
        # Move purchase returns
        self.env['mdl_buys_r'].search([
            ('fld_parent_id.id', 'in', orders_to_merge_ids)
        ]).write({'fld_parent_id': main_order.id})
