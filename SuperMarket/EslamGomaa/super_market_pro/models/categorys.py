from odoo import models, fields, api, _


class cls_categorys(models.Model):
    _name = 'mdl_categorys'
    _description = 'Table Of Goods Categorys'
    _order = "name"
    _sql_constraints = [('uniqueCategoryName', 'unique (name)', 'The Name Is Existe Before')]

    name = fields.Char(string='Tag Name', required=True)
    fld_description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
