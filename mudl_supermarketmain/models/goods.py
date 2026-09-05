from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_goods(models.Model):
    _name = 'mdl_goods'
    _description = 'Table Of All Goods'
    _order = "fld_class_id, name"

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    @api.constrains('name', 'fld_class_id')
    def fnc_unique_field(self):
        if self.search([('name', '=', self.name), ('fld_class_id', '=', self.fld_class_id.id), ('id', '!=', self.id)]):
            raise ValidationError(_('The Goods Is Existing Before'))

    fld_class_id = fields.Many2one('mdl_classes', string="Class Name", required=True, ondelete="restrict")
    name = fields.Char(string='Name', required=True, index=True)
    fld_price_buy = fields.Float(string='Price Buy', required=True, digits=(8, 2))
    fld_price_qst = fields.Float(string='Price Qst', required=True, digits=(8, 2))
    fld_price_cash = fields.Float(string='Price Cash', required=True, digits=(8, 2))
    fld_hafz = fields.Float(string='Goods Hafez', required=True, digits=(8, 2))
    fld_alarms = fields.Integer(string='Alarms', default=1)
    fld_description = fields.Text(string='Description')
    fld_notes = fields.Text(string='Notes')
    fld_qst = fields.Float(string='Qest Monthy', digits=(8, 2))
    fld_qst_num = fields.Integer(string='Count Qest In Month')
    fld_moqdm = fields.Float(string='El Moqadem', digits=(8, 2))
    active = fields.Boolean(default=True)
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')

