from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_sale_on_low_balance = fields.Boolean(related='company_id.restrict_sale_on_low_balance', readonly=False)