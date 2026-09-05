from odoo import models, fields, api


class HmsDoctor(models.Model):
    _name = "hms.doctor"

    name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    img = fields.Image(max_width=100, max_height=100)