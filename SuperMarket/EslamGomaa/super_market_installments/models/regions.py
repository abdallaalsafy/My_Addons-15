from odoo import api, fields, models, _


class Cls_regions(models.Model):
    _name = 'mdl_regions'
    _description = "Table Of All Regions"
    _order = "name"
    _sql_constraints = [('UniqueRegionsName', 'unique (name)', 'The Name Of Region Is Existe Before')]

    name = fields.Char(string="Name", required=True, index=True)
    active = fields.Boolean(default=True)
    fld_notes = fields.Text(string='Notes')


