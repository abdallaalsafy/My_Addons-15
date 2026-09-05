from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

class cls_sells(models.Model):
    _inherit = 'mdl_sells'

    # ========================= Basic Fields =========================
    fld_is_qst = fields.Boolean(string="Is Sells Qst?", default=False)
    fld_num_isalls = fields.Integer(string="Number Of Isalls")
    fld_date_first_qst = fields.Date(string="Date Of The First Isall", default=lambda self: fields.Date.today())
    
    # ========================= Related Fields =========================
    fld_phone = fields.Char(related="fld_customer_id.fld_phone")
    fld_region_id = fields.Many2one(related="fld_customer_id.fld_region_id")
    fld_place_id = fields.Many2one(related="fld_customer_id.fld_place_id")
    fld_address = fields.Char(related="fld_customer_id.fld_address")
    
    # ========================= Mandoops Fields =========================
    fld_mandoops = fields.Many2many('mdl_mandoops', string="Mandoops", ondelete='restrict')
    fld_collector_id = fields.Many2one('mdl_mandoops', string="Collector", ondelete='restrict')
    
    # ========================= Computed Fields =========================
    fld_total_qst = fields.Float(string='Total Qest', compute='_compute_totals_qst', store=True)
    fld_remain_qst = fields.Float(string='Remain Qest', compute='_compute_totals_qst',  store=True)
    fld_win_qst = fields.Float(string='Winning Qest', compute='_compute_totals_qst', store=True)
    fld_total_hafez = fields.Float(string='Total Hafez', compute='_compute_totals_qst', store=True)
    
    # ========================= Relations =========================
    fld_isalls_ids = fields.One2many('mdl_isalls', 'fld_sell_id', string="Installments", compute='_compute_create_isalls', store=True)


    # ========================= Compute Functions =========================
    @api.depends( 'fld_sells_goods_ids.fld_clc_qst','fld_sells_goods_ids.fld_clc_hafez', 'fld_sells_goods_ids.fld_win_qst',
                  'fld_paying', 'fld_discount', 'fld_discount_percent')
    def _compute_totals_qst(self):
        """Compute total, remain, and winning amounts with both discount types"""
        for record in self:
            # Calculate total from goods
            total_qst = sum(goods.fld_clc_qst for goods in record.fld_sells_goods_ids)
            total_hafez = sum(goods.fld_clc_hafez for goods in record.fld_sells_goods_ids)
            record.fld_total_qst = total_qst
            record.fld_total_hafez = total_hafez

            # Calculate total discount (fixed + percentage)
            paying = record.fld_paying or 0
            fixed_discount = record.fld_discount or 0
            percent_discount = 0

            if record.fld_discount_percent and total_qst > 0:
                percent_discount = (record.fld_discount_percent / 100) * total_qst

            total_discount = fixed_discount + percent_discount
            record.fld_remain_qst = total_qst - paying - total_discount

            # Calculate winning
            win = sum(goods.fld_win_qst for goods in record.fld_sells_goods_ids)
            record.fld_win_qst = win + total_discount

    @api.depends('fld_remain_qst', 'fld_date_first_qst', 'fld_num_isalls', 'fld_is_qst', 'fld_date')
    def _compute_create_isalls(self):
        for record in self:
            isall_lst = []
            qset = 0
            added_qset = 0
            is_qst = record.fld_is_qst
            num_isalls = record.fld_num_isalls or 0
            date_first_qst = record.fld_date_first_qst
            date_sell = record.fld_date
            remain_qst = record.fld_remain_qst or 0
            
            # Calculate first installment date
            date_first = False
            if date_sell or date_first_qst:
                date_first = date_first_qst if date_first_qst else date_sell + relativedelta(months=1)
            
            # Calculate installment amount
            if remain_qst >= num_isalls and num_isalls > 0:
                qset = remain_qst // num_isalls
            
            # Clear existing installments
            record.fld_isalls_ids = [(5,)]
            
            # Create new installments
            if date_first and qset > 0 and is_qst:
                for index in range(0, int(num_isalls)):
                    reg_date = date_first + relativedelta(months=index)
                    isall_data = {
                        'fld_reg_date': reg_date,
                        'fld_amount': qset,
                        'fld_num': index + 1,
                        'fld_month': reg_date.month,
                        'fld_year': reg_date.year,
                    }
                    isall_lst.append((0, 0, isall_data))
                    added_qset += qset
                    
                    # Calculate remaining amount for next installments
                    remainder = remain_qst - added_qset
                    if index != num_isalls - 1:
                        qset = remainder // (num_isalls - 1 - index)
                
                record.fld_isalls_ids = isall_lst
