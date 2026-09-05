from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_buys_goods(models.Model):
    _name = 'mdl_buys_goods'
    _description = 'Table Of All Fatoras Buy Goods'

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.depends('fld_goods_num', "fld_price_buy")
    def fnc_calc_price(self):
        for rcrd in self:
            rcrd.fld_calc_price = rcrd.fld_goods_num * rcrd.fld_price_buy

    @api.onchange('fld_class_id')
    def fnc_class_changed(self):
        if (self.fld_class_id and self.fld_class_id != self.fld_goods_id.fld_class_id) or not self.fld_class_id:
            self.fld_goods_id = False

    @api.onchange('fld_goods_id')
    def fnc_goods_changed(self):
        if self.fld_goods_id:
            self.fld_price_buy = self.fld_goods_id.fld_price_buy
        else:
            self.fld_price_buy = 0

    @api.onchange('fld_goods_num')
    def fnc_nozero_numgoods(self):
        if self.fld_goods_num <= 0:
            self.fld_goods_num = 1

    @api.onchange("fld_price_buy")
    def fnc_nozero_prices(self):
        vrb = self.fld_goods_id
        if vrb and self.fld_price_buy <= 0:
            old_price = self.search([('fld_goods_id', '=', vrb.id), ('fld_buy_id', '=', self._origin.fld_buy_id.id)])
            if old_price:
                self.fld_price_buy = old_price.fld_price_buy
            else:
                self.fld_price_buy = vrb.fld_price_buy

    fld_goods_num = fields.Integer(string='Count Of Goods', required=True, default=1)
    fld_price_buy = fields.Float(string='Price Buy Of Goods', digits=(8, 2))
    fld_calc_price = fields.Float(string='Calc Price Buy', digits=(8, 2), store=True, compute='fnc_calc_price')
    fld_class_id = fields.Many2one('mdl_classes', string="Class Name", required=True, ondelete="restrict")
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods Name", required=True, ondelete="restrict",
                                   domain="[('fld_class_id', '=', fld_class_id)]")
    fld_buy_id = fields.Many2one('mdl_buys', string="Fatora Buy", required=True, ondelete="cascade")
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')
