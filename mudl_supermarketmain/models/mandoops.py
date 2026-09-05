from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_mandoops(models.Model):
    _name = 'mdl_mandoops'
    _description = 'Table Of All Mandoops'
    _order = "name"
    _sql_constraints = [('unique_mandoops_name', 'unique (name)', 'The Name Is Existe Before')]

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    name = fields.Char(string='Name', required=True, index=True)
    fld_phone = fields.Text(string='Phone')
    fld_address = fields.Text(string='Address')
    fld_salary = fields.Float(string='Salary', digits=(8, 2))
    active = fields.Boolean(default=True)
    fld_notes = fields.Text(string='Notes')
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')

            