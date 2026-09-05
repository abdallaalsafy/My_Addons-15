from odoo import api, fields, models, _


class ProductProduct(models.Model):
    """
        Inherit Product Product:
    """
    _inherit = 'product.product'

    bonus = fields.Float(
        string="Bonus"
    )

