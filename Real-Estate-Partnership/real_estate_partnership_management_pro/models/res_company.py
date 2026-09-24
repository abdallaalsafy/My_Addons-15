from odoo import models, fields, api



class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_sale_on_low_balance = fields.Boolean(string='Restrict Sale on Low Balance',
                                                  help='If enabled, property sale will be restricted when any partner has balance less than their partnership amount.')
    auto_create_transaction_default = fields.Boolean(default=True,
                                    string='Auto-create Transaction for Partnership Payments by Default',
                                    help='Default value of the "Auto-create Transaction" option when a new partnership payment is created. '
                                        'Users can still change it per payment before saving.')