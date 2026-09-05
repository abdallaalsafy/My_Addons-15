from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_stores(models.Model):
    _name = 'mdl_stores'
    _description = 'Table Of All Stores'
    _order = "name"
    _sql_constraints = [('unique_stores_name', 'unique (name)', 'The Name Is Existe Before')]

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    name = fields.Char(string='Name', required=True, index=True)
    active = fields.Boolean(string="Active", default=True)
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')

