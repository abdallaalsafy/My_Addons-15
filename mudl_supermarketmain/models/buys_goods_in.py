from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_buys_goods_in(models.Model):
    _name = 'mdl_buys_goods_in'
    _description = 'Table Of All Fatoras Buys Goods In'

    @api.onchange('fld_class_id')
    def fnc_class_changed(self):
        if (self.fld_class_id and self.fld_class_id != self.fld_goods_id.fld_class_id) or not self.fld_class_id:
            self.fld_goods_id = False

    fld_class_id = fields.Many2one('mdl_classes', required=True, ondelete="restrict")
    fld_goods_id = fields.Many2one('mdl_goods', required=True, ondelete="restrict",
                                   domain="[('fld_class_id', '=', fld_class_id)]")
    fld_goods_num = fields.Integer(required=True)
    fld_buy_id = fields.Many2one('mdl_buys', required=True, ondelete="SET NULL")
    fld_goods_num_buy = fields.Integer(required=True)
    fld_action = fields.Selection([('Create', 'Create Buy'), ('Update', 'Update Buy'), ('Delete', 'Delete Buy')], required=True)
    fld_buy_id_action = fields.Char(required=True)
    fld_store_id = fields.Many2one('mdl_stores', required=True, ondelete="restrict")
    fld_goods_num_store = fields.Integer(required=True)
