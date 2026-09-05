from odoo import models, fields, api, _

class cls_sells_r(models.Model):
    _inherit = 'mdl_sells_r'

    fld_is_qst = fields.Boolean(related="fld_parent_id.fld_is_qst", string="Is Return Qst?", store=True)
    # ========================= Computed Fields =========================
    fld_total_qst = fields.Float(string='Total Qest', compute='_compute_totals_qst_r', store=True)
    fld_remain_qst = fields.Float(string='Remain Qest', compute='_compute_totals_qst_r', store=True)
    fld_win_qst = fields.Float(string='Winning Return Qest', compute='_compute_totals_qst_r', store=True)
    fld_total_hafez = fields.Float(string='Total Hafez', compute='_compute_totals_qst_r', store=True)

    # ========================== Compute Functions ==========================
    @api.depends('fld_sells_r_goods_ids.fld_clc_qst', 'fld_sells_r_goods_ids.fld_clc_hafez',
                 'fld_sells_r_goods_ids.fld_win_qst',
                 'fld_paying', 'fld_discount', 'fld_discount_percent')
    def _compute_totals_qst_r(self):
        """Compute total, remain, and winning amounts with both discount types"""
        for record in self:
            # Calculate total from goods
            total_qst = sum(goods.fld_clc_qst for goods in record.fld_sells_r_goods_ids)
            total_hafez = sum(goods.fld_clc_hafez for goods in record.fld_sells_r_goods_ids)
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
            win = sum(goods.fld_win_qst for goods in record.fld_sells_r_goods_ids)
            record.fld_win_qst = win - total_discount



