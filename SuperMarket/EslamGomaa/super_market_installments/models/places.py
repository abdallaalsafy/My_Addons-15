from odoo import api, fields, models, _


class Cls_places(models.Model):
    _name = 'mdl_places'
    _description = "Table Of All Places"
    _order = "fld_region_id,name"
    _sql_constraints = [('UniquePlacesName', 'unique (name,fld_region_id)', 'The Name Of Place Is Existe Before')]

    name = fields.Char(string="Name", required=True, index=True)
    fld_region_id = fields.Many2one("mdl_regions", string="Region", required=True, ondelete="restrict")
    active = fields.Boolean(default=True)
    fld_notes = fields.Text(string='Notes')


