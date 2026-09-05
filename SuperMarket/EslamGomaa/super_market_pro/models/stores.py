from odoo import api, fields, models, _

class cls_stores(models.Model):
    _name = 'mdl_stores'
    _description = 'Table Of All Stores'
    _order = "name"
    _sql_constraints = [('uniqueStoreName', 'unique (name)', 'The Name Is Existe Before')]

    name = fields.Char(string='Name', required=True, index=True)
    fld_notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
