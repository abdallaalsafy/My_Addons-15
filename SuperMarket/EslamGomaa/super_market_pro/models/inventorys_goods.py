from odoo import models, fields, api, _


class cls_inventorys_goods(models.Model):
    _name = 'mdl_inventorys_goods'
    _description = 'Table Of Inventory Goods'

    fld_category_id = fields.Many2one(related='fld_goods_id.fld_category_id', string="Category", store=True)
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods",domain="[('fld_category_id', '=?', fld_category_id)]",ondelete='restrict')
    fld_count = fields.Float(string='Count', )
    fld_inventory_id = fields.Many2one('mdl_inventorys', string="Inventory ID",ondelete='cascade')
    fld_unit_id = fields.Many2one(related='fld_goods_id.fld_unit_id', string="Unit",store=True)
