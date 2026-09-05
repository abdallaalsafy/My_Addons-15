from odoo import models, fields, api, _

class cls_mandoops_goods(models.Model):
    _name = 'mdl_mandoops_goods'
    _auto = False
    _description = 'Table Of Mandoops Goods'
    _order = "mdl_mandoops_id,fld_category_id,fld_goods_id"

    mdl_mandoops_id = fields.Many2one("mdl_mandoops", string="Mandoop")
    fld_category_id = fields.Many2one(related='fld_goods_id.fld_category_id', string="Category")
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods")
    fld_unit_id = fields.Many2one(related='fld_goods_id.fld_unit_id')
    fld_total_qst_mandoop = fields.Float(string='Total Qest')
    fld_total_sell_mandoop = fields.Float(string='Total Cash')
    fld_total_hafez_mandoop = fields.Float(string='Total Hafez')
    fld_total_sells = fields.Float(string='Total Sells')
    fld_count = fields.Float(string="Count Goods")
    fld_win_mandoop = fields.Float(string='Winning', )