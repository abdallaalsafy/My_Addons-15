from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class cls_merg_sells_extended(models.TransientModel):
    """
    Extended Wizard for Merging Sales Orders with Installment Support
    This wizard inherits from the base merge wizard and adds installment-specific functionality
    for the super_market_installments module.
    """
    _inherit = 'wzrd_merg_sells'
    _description = 'Extended Wizard for Merging Sales Orders with Installments'

    # Additional fields for installment handling
    fld_is_qst = fields.Boolean(
        string="Is Sells Qst?",
        help="Whether the merged order should be treated as an installment sale"
    )
    
    fld_num_isalls = fields.Integer(
        string="Number Of Installments",
        help="Number of installments for the merged order"
    )
    
    fld_date_first_qst = fields.Date(
        string="Date Of First Installment",
        help="Date when the first installment should be due",
        
    )
    
    fld_collector_id = fields.Many2one(
        'mdl_mandoops',
        string="Collector",
        help="Collector responsible for the installments",
        ondelete='restrict'
    )
    
    fld_mandoops = fields.Many2many(
        'mdl_mandoops',
        string="Mandoops",
        help="Mandoops assigned to the merged order",
        ondelete='restrict'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values including installment status"""
        res = super().default_get(fields_list)
        
        if self._context.get('active_ids'):
            active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
            if active_ids:
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

    
    def _handle_installment_merge(self, active_ids, min_rcrd):
        """
        Handle installment-specific merge logic
        
        Args:
            active_ids: All sales orders being merged
            min_rcrd: Main sales order (earliest date)
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
        customer = min_rcrd.fld_customer_id
        mandoops = self.fld_mandoops or min_rcrd.fld_mandoops
        collector = self.fld_collector_id or min_rcrd.fld_collector_id
        date_first_qst = self.fld_date_first_qst or min_rcrd.fld_date_first_qst
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
            date_first_qst = min_rcrd.fld_date + relativedelta(months=1)
        
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
        
        min_rcrd.write(update_vals)

    def _calculate_totals(self, sales_orders):
        """
        Override to add installment totals calculation
        
        Args:
            sales_orders: Recordset of sales orders
            
        Returns:
            dict: Dictionary with calculated totals including installment fields
        """
        totals = super()._calculate_totals(sales_orders)
        
        # Add installment-specific totals
        totals.update({
            'total_qst': 0.0,
            'total_win_qst': 0.0,
            'total_hafez': 0.0,
            'total_remain_qst': 0.0,
        })
        
        for order in sales_orders:
            totals['total_qst'] += order.fld_total_qst or 0.0
            totals['total_win_qst'] += order.fld_win_qst or 0.0
            totals['total_hafez'] += order.fld_total_hafez or 0.0
            totals['total_remain_qst'] += order.fld_remain_qst or 0.0
        
        return totals

    def _perform_merge_operation(self, sales_orders, main_order, totals, customer):
        """
        Override to add installment-specific merge operations
        
        Args:
            sales_orders: Recordset of sales orders to merge
            main_order: Main sales order to keep
            totals: Dictionary with calculated totals
            customer: Customer record
        """
        # Call parent method for basic merge operation
        super()._perform_merge_operation(sales_orders, main_order, totals, customer)
        
        # Add installment-specific updates if needed
        if self.fld_is_qst or any(order.fld_is_qst for order in sales_orders):
            self._handle_installment_merge(sales_orders, main_order)

    def _move_related_records(self, orders_to_merge_ids, main_order):
        """
        Override to add installment records movement
        
        Args:
            orders_to_merge_ids: List of order IDs to merge
            main_order: Main sales order
        """
        # Call parent method for basic record movement
        super()._move_related_records(orders_to_merge_ids, main_order)
        
        # Move installment records
        self.env['mdl_isalls'].search([
            ('fld_sell_id.id', 'in', orders_to_merge_ids)
        ]).write({'fld_sell_id': main_order.id})
