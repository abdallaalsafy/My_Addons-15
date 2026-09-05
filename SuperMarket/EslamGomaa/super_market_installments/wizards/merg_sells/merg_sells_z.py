from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class cls_merg_sells(models.TransientModel):
    _inherit = 'wzrd_merg_sells'
    
    # Additional fields for installment handling
    fld_is_qst = fields.Boolean(string="Is Sells Qst?")
    
    @api.model
    def default_get(self, fields_list):
        """Set default values including installment status"""
        res = super().default_get(fields_list)
        if self._context.get('active_ids'):
            active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
            if active_ids:
                # Set installment status based on first order
                res['fld_is_qst'] = active_ids[0].fld_is_qst
        return res

    def fnc_create_isalls(self, num_isalls, date_first_qst, remain_qst):
        """Create installment records for merged order"""
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
        """Enhanced merge with installment support"""
        try:
            # Call parent method for basic merge functionality
            result = super().fnc_merging_sells()
            
            # Handle installment-specific logic
            active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
            if len(active_ids) == 1:
                raise UserError(_('You Must Merge More Than One Sells!'))
            
            # Find main order (earliest date)
            min_date = min(active_ids.mapped('fld_date'))
            min_date_id = min(active_ids.filtered(lambda lm: lm.fld_date == min_date).ids)
            min_rcrd = active_ids.filtered(lambda lm: lm.id == min_date_id)
            
            # Get installment-related data
            is_qst = self.fld_is_qst or min_rcrd.fld_is_qst
            max_num_isalls = max(active_ids.mapped('fld_num_isalls'))
            
            if is_qst:
                self._handle_installment_merge(active_ids, min_rcrd, max_num_isalls)
            
            return result
            
        except Exception as e:
            raise UserError(_('Failed to merge sales orders: %s') % str(e))
    
    def _handle_installment_merge(self, active_ids, min_rcrd, max_num_isalls):
        """Handle installment-specific merge logic"""
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
        mandoops = min_rcrd.fld_mandoops
        collector = min_rcrd.fld_collector_id
        date_first_qst = min_rcrd.fld_date_first_qst
        
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
        isalls_lst = self.fnc_create_isalls(max_num_isalls, date_first_qst, remain_qst)
        
        # Update main order with installment data
        update_vals = {
            'fld_total_qst': totl_qst,
            'fld_total_hafez': totl_hafez,
            'fld_win_qst': totl_win_qst,
            'fld_remain_qst': remain_qst,
            'fld_customer_id': customer.id if customer else False,
            'fld_mandoops': [(6, 0, mandoops.ids)] if mandoops else False,
            'fld_collector_id': collector.id if collector else False,
            'fld_num_isalls': max_num_isalls,
            'fld_date_first_qst': date_first_qst,
            'fld_isalls_ids': [(5, 0)] + isalls_lst,  # Clear existing and add new
        }
        
        min_rcrd.write(update_vals)
