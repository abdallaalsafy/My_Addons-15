from odoo import models, fields, api, _
from odoo.exceptions import UserError

class cls_merg_sells_r(models.TransientModel):
    _inherit = 'wzrd_merg_sells_r'

    def fnc_merging_sells_r(self):
        totl_sell=0
        remain_sell = 0
        totl_qst = 0
        totl_hafez = 0
        remain_qst = 0
        paying=0
        discount = 0
        ids_lst=[]
        active_ids = self.env['mdl_sells_r'].browse(self._context.get('active_ids'))
        if len(active_ids) == 1: raise UserError(_('You Must Mergine More Than One Return Sells!'))
        ###### Get Parent Sells For Return Sells ########################
        group_prnt=active_ids.read_group([],['fld_parent_id'],groupby=['fld_parent_id'])
        count_group=0
        prnt_id = 0
        prnt_rcrd = False
        if len(group_prnt)>1:
            for grp in group_prnt:
                xtupl=grp['fld_parent_id']
                if xtupl==False:continue
                prnt_id=xtupl[0]
                count_group+=1
            if count_group > 1:raise UserError(_('Must There Is One Parent Only!'))
        else:
            xfld=group_prnt[0]['fld_parent_id']
            if xfld:prnt_id=xfld[0]
        if prnt_id>0:prnt_rcrd=self.env['mdl_sells'].browse(prnt_id)
        ###########################################################
        min_date= min(active_ids.mapped ('fld_date'))
        min_date_id = min(active_ids.filtered(lambda lm:lm.fld_date==min_date).ids)
        min_rcrd=active_ids.filtered(lambda lm:lm.id==min_date_id)
        customer =min_rcrd.fld_customer_id
        if not customer:
            rcrd_customer = active_ids.filtered(lambda lm: lm.fld_customer_id)
            if rcrd_customer:contact=rcrd_customer[0].fld_customer_id
        for rcrd in active_ids:
            if rcrd!=min_rcrd:ids_lst.append(rcrd.id)
            totl_sell+=rcrd.fld_total
            remain_sell += rcrd.fld_remain
            totl_qst += rcrd.fld_total_qst
            totl_hafez += rcrd.fld_total_hafez
            remain_qst += rcrd.fld_remain_qst
            paying+=rcrd.fld_paying
            discount += rcrd.fld_discount
        min_rcrd.write({'fld_total':totl_sell,
                        'fld_remain':remain_sell,
                        'fld_total_qst': totl_qst,
                        'fld_total_hafez': totl_hafez,
                        'fld_remain_qst': remain_qst,
                        'fld_paying':paying,
                        'fld_discount': discount,
                        'fld_customer_id':customer.id,
                        'fld_parent_id':prnt_rcrd})
        self.env['mdl_sells_r_goods'].search([('fld_sells_r_id.id','in',ids_lst)]).write({'fld_sells_r_id':min_rcrd})
        self.env['mdl_customers_out'].search([('fld_sells_r_id.id', 'in', ids_lst),('fld_is_pay','=', False)]).write({'fld_sells_r_id': min_rcrd})
        self.env['mdl_sells_r'].browse(ids_lst).unlink()
