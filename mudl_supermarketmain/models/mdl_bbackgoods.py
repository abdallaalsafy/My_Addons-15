from odoo import models, fields, api, _
from mudl_supermarketmain.public_class import MainClass


class ClsBbackGoods(models.Model):
    _name = 'tbl_bbackgoods'
    _description = 'Table Of All Fatoras Buy Back Goods'

    def fnc_renum(self): MainClass().fnc_renum(self)
# OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    @api.depends('fld_goods_num', "fld_goods_price_buy")
    def fnc_price_in_num(self): self.fld_price_in_num = self.fld_goods_num * self.fld_goods_price_buy
# OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO

    @api.onchange('fld_class_id')
    def fnc_class_changed(self):  # دالة تمسح نوع المنتج أو تجلبه إذا تغير صنف المنتج
        if (self.fld_class_id and self.fld_class_id != self.fld_goods_id.fld_class_id) or not self.fld_class_id:
            self.fld_goods_id = False

    @api.onchange('fld_goods_id')  # دالة تغير رقم وسعر المنتج إذا تغير نوع المنتج
    def fnc_goods_changed(self):
        self.fld_goods_price_buy = self.fld_goods_id.fld_price_buy

    @api.onchange('fld_goods_num')   # دالة تجعل عدد المنتج لا يكون صفر
    def fnc_nozero_numgoods(self):
        if self.fld_goods_num <= 0:
            self.fld_goods_num = 1

    @api.onchange("fld_goods_price_buy")
    def fnc_nozero_prices(self):  # دالة لا تجعل سعر المنتج صفر مادام هناك منتج مختار
        vrb = self.fld_goods_id
        if vrb and self.fld_goods_price_buy <= 0:
            self.fld_goods_price_buy = vrb.fld_price_buy
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    fld_goods_num = fields.Integer(string='Count Of Goods', required=True, default=1)
    fld_goods_price_buy = fields.Float(string='Price Buy Of Goods', digits=(8, 2))
    fld_price_in_num = fields.Float(string='Calc Price Buy Of Goods Num', digits=(8, 2), store=True, compute='fnc_price_in_num')
    fld_class_id = fields.Many2one('tbl_classes', string="Class Name", required=True, ondelete="restrict")
    fld_goods_id = fields.Many2one('tbl_goods', string="Goods Name", required=True, ondelete="restrict", domain="[('fld_goods_del', '=', False),('fld_class_id', '=', fld_class_id)]")
    fld_bback_id = fields.Many2one('tbl_bbacks', string="Fatora Buy Back ID", required=True, ondelete="cascade")
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')