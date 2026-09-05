from odoo import api, fields, models, _


class ResRegion(models.Model):
    _name = 'res.region'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Res Region"
    _rec_name = 'name'
    _order = "name, id"

    name = fields.Char(
        string="Name"
    )


