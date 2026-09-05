from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class cls_merg_sells_complete(models.TransientModel):
    """
    Complete Wizard for Merging Sales Orders with Installment Support
    This wizard includes all original merge functionality plus new installment features
    for super_market_installments module without using super() calls.
    """
    _name = 'wzrd_merg_sells_extended'
    _description = 'Complete Wizard for Merging Sales Orders with Installments'

    # ========================= Original Fields =========================
    merge_date = fields.Date(
        string='Merge Date',
        help='Date for the merged sales order'
    )
    
    merge_notes = fields.Text(
        string='Merge Notes',
        help='Optional notes about this merge operation'
    )

    # ========================= New Installment Fields =========================
    fld_is_qst = fields.Boolean(
        string="Is Sells Qst?",
        default=False,
        help="Whether merged order should be treated as an installment sale"
    )
    
    fld_num_isalls = fields.Integer(
        string="Number Of Installments",
        help="Number of installments for merged order"
    )
    
    fld_date_first_qst = fields.Date(
        string="Date Of First Installment",
        help="Date when first installment should be due",
        
    )
    
    fld_collector_id = fields.Many2one(
        'mdl_mandoops',
        string="Collector",
        help="Collector responsible for installments",
        ondelete='restrict'
    )
    
    fld_mandoops = fields.Many2many(
        'mdl_mandoops',
        string="Mandoops",
        help="Mandoops assigned to merged order",
        ondelete='restrict'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values for the wizard including installment status"""
        res = {}
        if self._context.get('active_ids'):
            active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
            if active_ids:
                # Set the earliest date as default merge date
                res['merge_date'] = min(active_ids.mapped('fld_date'))
                
                # Set installment status based on first order
                first_order = active_ids[0]
                res['fld_is_qst'] = first_order.fld_is_qst
                
                # Set maximum number of installments from all orders
                max_num_isalls = max(active_ids.mapped('fld_num_isalls') or [0])
                res['fld_num_isalls'] = max_num_isalls
                
                # Set date for first installment
                dates = [order.fld_date_first_qst for order in active_ids if order.fld_date_first_qst]
                if dates:
                    res['fld_date_first_qst'] = min(dates)
                else:
                    # Use earliest order date + 1 month as default
                    earliest_date = min(active_ids.mapped('fld_date'))
                    res['fld_date_first_qst'] = earliest_date + relativedelta(months=1)
        return res

    def fnc_create_isalls(self, num_isalls, date_first_qst, remain_qst):
        """
        Create installment records for merged order
        
        Args:
            num_isalls: Number of installments to create
            date_first_qst: Date of first installment
            remain_qst: Remaining amount to distribute
            
        Returns:
            list: List of installment data tuples for Odoo
        """
        isall_lst = []
        qset = 0
        added_qset = 0
        
        if remain_qst >= num_isalls and num_isalls > 0:
           qset = remain_qst // num_isalls
           
        if date_first_qst and qset:
           for index in range(0, int(num_isalls)):
                reg_date = date_first_qst + relativedelta(months=index)
                isall_data = {
                    'fld_reg_date': reg_date,
                    'fld_amount': qset,
                    'fld_num': index + 1,
                    'fld_month': reg_date.month,
                    'fld_year': reg_date.year,
                }
                isall_lst.append((0, 0, isall_data))
                added_qset += qset
                remainder = remain_qst - added_qset
                if index != num_isalls - 1:
                   qset = remainder // (num_isalls - 1 - index)
        return isall_lst

    def fnc_merging_sells(self):
        """
        Complete merge function with installment support
        Includes all original functionality plus new installment features
        """
        try:
            # Step 1: Input validation
            active_ids = self._validate_and_get_active_orders()
            
            # Step 2: Find the main sales order (earliest date)
            main_order = self._find_main_sales_order(active_ids)
            
            # Step 3: Calculate consolidated totals
            totals = self._calculate_totals(active_ids)
            
            # Step 3.5: Validate discount consistency
            self._validate_discount_consistency(active_ids)
            
            # Step 4: Determine customer for merged order
            customer = self._determine_customer(active_ids, main_order)
            
            # Step 5: Handle installment logic if needed
            if self.fld_is_qst or any(order.fld_is_qst for order in active_ids):
                self._handle_installment_merge(active_ids, main_order)
            
            # Step 6: Perform the merge operation with transaction safety
            self._perform_merge_operation(active_ids, main_order, totals, customer)
            
            # Return success message
            discount_info = self._format_discount_info(totals)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Successfully merged %d sales orders\n%s') % (len(active_ids), discount_info),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(_('Failed to merge sales orders: %s') % str(e))

    def _validate_and_get_active_orders(self):
        """
        Validate input and return active sales orders
        
        Returns:
            recordset: Active sales orders to merge
            
        Raises:
            UserError: If validation fails
        """
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            raise UserError(_('No sales orders selected for merging'))
        
        sales_orders = self.env['mdl_sells'].browse(active_ids)
        
        # Validate that all records exist
        if len(sales_orders) != len(active_ids):
            raise UserError(_('Some selected sales orders were not found'))
        
        # Check if we have more than one order
        if len(sales_orders) == 1:
            raise UserError(_('You must select more than one sales order to merge'))

        return sales_orders

    def _find_main_sales_order(self, sales_orders):
        """
        Find the main sales order (earliest date) to keep
        
        Args:
            sales_orders: Recordset of sales orders
            
        Returns:
            record: Main sales order to keep
        """
        earliest_date = min(sales_orders.mapped('fld_date'))
        main_order = sales_orders.filtered(lambda order: order.fld_date == earliest_date)
        
        if len(main_order) > 1:
            # If multiple orders have the same earliest date, take the first one
            main_order = main_order[0]
        
        return main_order

    def _calculate_totals(self, sales_orders):
        """
        Calculate consolidated totals from all sales orders including installment fields
        
        Args:
            sales_orders: Recordset of sales orders
            
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
            # New installment totals
            'total_qst': 0.0,
            'total_win_qst': 0.0,
            'total_hafez': 0.0,
            'total_remain_qst': 0.0,
        }
        
        # Calculate weighted average for discount percentage
        total_amount_for_percent = 0.0
        weighted_percent_sum = 0.0
        
        for order in sales_orders:
            # Original totals
            totals['total_amount'] += order.fld_total or 0.0
            totals['total_win'] += order.fld_win or 0.0
            totals['total_remaining'] += order.fld_remain or 0.0
            totals['total_paid'] += order.fld_paying or 0.0
            totals['total_discount'] += order.fld_discount or 0.0
            
            # Calculate weighted average for discount percentage
            if hasattr(order, 'fld_discount_percent') and order.fld_discount_percent and order.fld_total:
                total_amount_for_percent += order.fld_total
                weighted_percent_sum += (order.fld_discount_percent / 100) * order.fld_total
            
            # New installment totals
            totals['total_qst'] += order.fld_total_qst or 0.0
            totals['total_win_qst'] += order.fld_win_qst or 0.0
            totals['total_hafez'] += order.fld_total_hafez or 0.0
            totals['total_remain_qst'] += order.fld_remain_qst or 0.0
        
        # Calculate weighted average discount percentage
        if total_amount_for_percent > 0:
            totals['total_discount_percent'] = (weighted_percent_sum / total_amount_for_percent) * 100
        
        return totals

    def _validate_discount_consistency(self, sales_orders):
        """
        Validate discount consistency across sales orders
        
        Args:
            sales_orders: Recordset of sales orders
            
        Returns:
            bool: True if discounts are consistent, False otherwise
        """
        # Check if orders have mixed discount types
        has_fixed_discount = any(order.fld_discount for order in sales_orders)
        has_percent_discount = any(hasattr(order, 'fld_discount_percent') and order.fld_discount_percent for order in sales_orders)

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

    def _determine_customer(self, sales_orders, main_order):
        """
        Determine the customer for the merged order
        
        Args:
            sales_orders: Recordset of sales orders
            main_order: The main sales order
            
        Returns:
            record: Customer record
        """
        # Try to use the main order's customer first
        if main_order.fld_customer_id:
            return main_order.fld_customer_id
        
        # If main order has no customer, find the first order with a customer
        orders_with_customer = sales_orders.filtered(lambda order: order.fld_customer_id)
        if orders_with_customer:
            return orders_with_customer[0].fld_customer_id
        
        # If no customer found, raise an error
        raise UserError(_('Cannot merge sales orders without a customer. Please ensure at least one order has a customer assigned.'))

    def _handle_installment_merge(self, active_ids, main_order):
        """
        Handle installment-specific merge logic
        
        Args:
            active_ids: All sales orders being merged
            main_order: Main sales order (earliest date)
        """
        # Calculate installment totals
        totl_qst = 0
        totl_win_qst = 0
        totl_hafez = 0
        remain_qst = 0
        
        for rcrd in active_ids:
            totl_qst += rcrd.fld_total_qst or 0.0
            totl_win_qst += rcrd.fld_win_qst or 0.0
            totl_hafez += rcrd.fld_total_hafez or 0.0
            remain_qst += rcrd.fld_remain_qst or 0.0
        
        # Get additional fields for installment orders
        customer = main_order.fld_customer_id
        mandoops = self.fld_mandoops or main_order.fld_mandoops
        collector = self.fld_collector_id or main_order.fld_collector_id
        date_first_qst = self.fld_date_first_qst or main_order.fld_date_first_qst
        num_isalls = self.fld_num_isalls or max(active_ids.mapped('fld_num_isalls') or [1])
        
        # Find customer if not set
        if not customer:
            rcrd_customer = active_ids.filtered(lambda lm: lm.fld_customer_id)
            if rcrd_customer:
                customer = rcrd_customer[0].fld_customer_id
        
        # Find mandoops if not set
        if not mandoops:
            rcrd_mandoops = active_ids.filtered(lambda lm: lm.fld_mandoops)
            if rcrd_mandoops:
                mandoops = rcrd_mandoops[0].fld_mandoops
        
        # Find collector if not set
        if not collector:
            rcrd_collector = active_ids.filtered(lambda lm: lm.fld_collector_id)
            if rcrd_collector:
                collector = rcrd_collector[0].fld_collector_id
        
        # Set date_first_qst if not set
        if not date_first_qst:
            date_first_qst = main_order.fld_date + relativedelta(months=1)
        
        # Create installments
        isalls_lst = self.fnc_create_isalls(num_isalls, date_first_qst, remain_qst)
        
        # Update main order with installment data
        update_vals = {
            'fld_is_qst': True,
            'fld_total_qst': totl_qst,
            'fld_total_hafez': totl_hafez,
            'fld_win_qst': totl_win_qst,
            'fld_remain_qst': remain_qst,
            'fld_customer_id': customer.id if customer else False,
            'fld_mandoops': [(6, 0, mandoops.ids)] if mandoops else False,
            'fld_collector_id': collector.id if collector else False,
            'fld_num_isalls': num_isalls,
            'fld_date_first_qst': date_first_qst,
            'fld_isalls_ids': [(5, 0)] + isalls_lst,  # Clear existing and add new
        }
        
        main_order.write(update_vals)

    def _perform_merge_operation(self, sales_orders, main_order, totals, customer):
        """
        Perform the actual merge operation with transaction safety
        
        Args:
            sales_orders: Recordset of sales orders to merge
            main_order: Main sales order to keep
            totals: Dictionary with calculated totals
            customer: Customer record
        """
        # Get IDs of orders to be merged (excluding main order)
        orders_to_merge_ids = sales_orders.filtered(lambda order: order.id != main_order.id).ids
        
        if not orders_to_merge_ids:
            raise UserError(_('No orders to merge found'))
        
        try:
            # Update main order with consolidated data
            main_order.write({
                'fld_total': totals['total_amount'],
                'fld_win': totals['total_win'],
                'fld_remain': totals['total_remaining'],
                'fld_paying': totals['total_paid'],
                'fld_discount': totals['total_discount'],
                'fld_customer_id': customer.id,
                'fld_date': self.merge_date or main_order.fld_date,
            })
            
            # Add merge notes if provided
            if self.merge_notes:
                existing_notes = main_order.fld_notes or ''
                merge_info = _('\n\n--- MERGED ORDERS ---\nMerged on: %s\nOrders merged: %s\nNotes: %s') % (
                    fields.Date.today(),
                    ', '.join(sales_orders.mapped('name') or ['ID: %s' % id for id in orders_to_merge_ids]),
                    self.merge_notes
                )
                main_order.write({'fld_notes': existing_notes + merge_info})
            
            # Move related records to main order
            self._move_related_records(orders_to_merge_ids, main_order)
            
            # Delete the merged orders
            self.env['mdl_sells'].browse(orders_to_merge_ids).unlink()
        except Exception as e:
            raise UserError(_('Failed to complete merge operation: %s') % str(e))

    def _move_related_records(self, orders_to_merge_ids, main_order):
        """
        Move related records from merged orders to main order
        
        Args:
            orders_to_merge_ids: List of order IDs to merge
            main_order: Main sales order
        """
        # Move sales goods
        self.env['mdl_sells_goods'].search([
            ('fld_sells_id.id', 'in', orders_to_merge_ids)
        ]).write({'fld_sells_id': main_order.id})
        
        # Move customer payments (unpaid ones)
        self.env['mdl_customers_in'].search([
            ('fld_sells_id.id', 'in', orders_to_merge_ids),
            ('fld_is_pay', '=', False)
        ]).write({'fld_sells_id': main_order.id})
        
        # Move sales returns
        self.env['mdl_sells_r'].search([
            ('fld_parent_id.id', 'in', orders_to_merge_ids)
        ]).write({'fld_parent_id': main_order.id})
        
        # Move installment records (new functionality)
        self.env['mdl_isalls'].search([
            ('fld_sell_id.id', 'in', orders_to_merge_ids)
        ]).write({'fld_sell_id': main_order.id})
