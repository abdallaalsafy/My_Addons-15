from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from mudl_supermarketmain.public_class import MainClass


class cls_customers(models.Model):
    _name = 'mdl_customers'
    _description = 'Table Of All Customers'
    _order = "name"
    _sql_constraints = [('unique_customers_name', 'unique (name)', 'The Name Is Existe Before')]

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    name = fields.Char(string='Name', required=True, index=True)
    fld_phone = fields.Text(string='Phone')
    fld_address = fields.Text(string='Address')
    active = fields.Boolean(default=True)
    fld_notes = fields.Text(string='Notes')
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')
