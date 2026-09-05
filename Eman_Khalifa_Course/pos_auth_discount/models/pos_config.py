from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    disc_password = fields.Char(string="Discount Password")