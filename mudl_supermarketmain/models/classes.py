import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.public_class import MainClass


class cls_classes(models.Model):
    _name = 'mdl_classes'
    _description = 'Table Of All Classes'
    _order = "name"
    _sql_constraints = [('unique_classes_name', 'unique (name)', 'The Name Is Existe Before')]

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    name = fields.Char(string='Name', required=True, index=True)
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')
