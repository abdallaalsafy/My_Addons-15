from odoo import models, fields, api



class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_sale_on_low_balance = fields.Boolean(string='Restrict Sale on Low Balance',
                                                  help='If enabled, property sale will be restricted when any partner has balance less than their investment amount')