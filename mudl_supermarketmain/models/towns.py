from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_towns(models.Model):
    _name = 'mdl_towns'
    _description = 'Table Of All Towns'
    _sql_constraints = [('unique_towns_name', 'unique (name)', 'The Name Is Existe Before')]

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    name = fields.Char(string='Name', required=True, index=True)

