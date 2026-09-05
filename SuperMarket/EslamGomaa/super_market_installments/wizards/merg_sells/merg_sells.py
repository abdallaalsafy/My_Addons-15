from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class cls_merg_sells(models.TransientModel):
    _inherit = 'wzrd_merg_sells'

    def fnc_get_default(self):
        active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
        return active_ids[0].fld_is_qst

    def fnc_create_isalls(self,num_isalls,date_first_qst,remain_qst):
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
                    'fld_year': reg_date.year, }
                isall_lst.append((0, 0, isall_data))
                added_qset += qset
                remainder = remain_qst - added_qset
                if index != num_isalls - 1:
                   qset = remainder // (num_isalls - 1 - index)
        return isall_lst

    def fnc_merging_sells(self):
        totl_sell=0
        totl_win=0
        remain_sell = 0
        totl_qst = 0
        totl_win_qst = 0
        totl_hafez = 0
        remain_qst = 0
        paying=0
        discount = 0
        isalls_lst = []
        ids_lst=[]
        active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
        if len(active_ids) == 1: raise UserError(_('You Must Mergine More Than One Sells!'))
        ###########################################################
        max_num_isalls = max(active_ids.mapped('fld_num_isalls'))
        min_date= min(active_ids.mapped ('fld_date'))
        min_date_id = min(active_ids.filtered(lambda lm:lm.fld_date==min_date).ids)
        min_rcrd=active_ids.filtered(lambda lm:lm.id==min_date_id)
        is_qst = min_rcrd.fld_is_qst
        customer = min_rcrd.fld_customer_id
        mandoops = min_rcrd.fld_mandoops
        collector = min_rcrd.fld_collector_id
        date_first_qst = min_rcrd.fld_date_first_qst
        if not customer:
            rcrd_customer = active_ids.filtered(lambda lm: lm.fld_customer_id)
            if rcrd_customer:customer=rcrd_customer[0].fld_customer_id
        if not mandoops:
            rcrd_mandoops = active_ids.filtered(lambda lm: lm.fld_mandoops)
            if rcrd_mandoops: mandoops = rcrd_mandoops[0].fld_mandoops
        if is_qst:
            if not collector:
                rcrd_collector = active_ids.filtered(lambda lm: lm.fld_collector_id)
                if rcrd_collector: collector = rcrd_collector[0].fld_collector_id
            if not date_first_qst:
                date_first_qst = min_rcrd.fld_date + relativedelta(months=1)

        for rcrd in active_ids:
            if rcrd!=min_rcrd:ids_lst.append(rcrd.id)
            totl_sell+=rcrd.fld_total
            totl_win+=rcrd.fld_win
            remain_sell += rcrd.fld_remain
            paying += rcrd.fld_paying
            discount += rcrd.fld_discount

            totl_qst += rcrd.fld_total_qst
            totl_win_qst += rcrd.fld_win_qst
            totl_hafez += rcrd.fld_total_hafez
            remain_qst += rcrd.fld_remain_qst
            if is_qst:
                min_rcrd.fld_isalls_ids = [(5,)]
                isalls_lst = self.fnc_create_isalls(max_num_isalls,date_first_qst,remain_qst)
        min_rcrd.write({'fld_total':totl_sell,
                        'fld_win':totl_win,
                        'fld_remain':remain_sell,
                        'fld_total_qst': totl_qst,
                        'fld_total_hafez': totl_hafez,
                        'fld_win_qst': totl_win_qst,
                        'fld_remain_qst': remain_qst,
                        'fld_paying':paying,
                        'fld_discount': discount,
                        'fld_customer_id':customer.id,
                        'fld_mandoops':mandoops,
                        'fld_collector_id':collector.id,
                        'fld_num_isalls':max_num_isalls,
                        'fld_date_first_qst':date_first_qst,
                        'fld_isalls_ids':isalls_lst})
        self.env['mdl_sells_goods'].search([('fld_sells_id.id','in',ids_lst)]).write({'fld_sells_id':min_rcrd})
        self.env['mdl_customers_in'].search([('fld_sells_id.id', 'in', ids_lst),('fld_is_pay','=', False)]).write({'fld_sells_id': min_rcrd})
        self.env['mdl_sells_r'].search([('fld_parent_id.id', 'in', ids_lst)]).write({'fld_parent_id': min_rcrd})
        self.env['mdl_sells'].browse(ids_lst).unlink()

    fld_is_qst = fields.Boolean(string="Is Sells Qst?", default=fnc_get_default)
