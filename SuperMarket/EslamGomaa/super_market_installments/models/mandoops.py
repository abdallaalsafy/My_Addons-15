from odoo import models, fields, api, _

class Cls_mandoops(models.Model):
    _name = 'mdl_mandoops'
    _description = 'Table Of All Mandoops'
    _order = "name"
    _sql_constraints = [('UniqueMandoopsName', 'unique (name)', 'The Name Of Mandoop Is Existe Before')]

    name = fields.Char(string='Name', required=True, index=True)
    fld_phone = fields.Char(string='Phone',size=11)
    fld_notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    fld_address = fields.Char(string='Address')
    fld_salary = fields.Float(string='Salary')