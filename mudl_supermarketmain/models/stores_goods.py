from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_stores_goods(models.Model):
    _name = 'mdl_stores_goods'
    _description = 'Table Of All Goods In Stores'

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.constrains('fld_goods_id', 'fld_store_id')
    def fnc_unique_field(self):
        for rcrd in self:
            if rcrd.search([('fld_goods_id', '=', rcrd.fld_goods_id.id), ('fld_store_id', '=', rcrd.fld_store_id.id),
                            ('id', '!=', rcrd.id)]):
                raise ValidationError(_('The Goods Is Existing Before To This Store'))

    fld_store_id = fields.Many2one('mdl_stores', string="Store Name", required=True, ondelete="restrict")
    fld_class_id = fields.Many2one('mdl_classes', string="Class Name", required=True, ondelete="restrict")
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods Name", required=True, ondelete="restrict",
                                   domain="[('fld_class_id', '=', fld_class_id)]")
    fld_goods_num = fields.Integer(string='Count Of Goods', required=True)
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')

