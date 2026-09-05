from odoo import models, fields, api, _

class cls_goods(models.Model):
    _inherit = 'mdl_goods'
    _sql_constraints = [('CheckGoodsPriceQst', 'check (fld_price_qst>0)', 'Price_Qest Must Be Above Zero')]


    fld_price_qst = fields.Float(string='Price Qest', required=True, )
    fld_hafez = fields.Float(string='Goods Hafez',compute='fnc_comput_hafez', store=True, )
    fld_ratio = fields.Float(string='Hafez Ratio %', )
    fld_type_hafez = fields.Selection(selection=[('ratio','Ratio'),('sum','Sum')], string="Hafez Type", default='sum', required=True)

    # ======================== Computed Functions ========================
    @api.depends('fld_type_hafez','fld_ratio','fld_price_qst')
    def fnc_comput_hafez(self):
        type_hafez = self.fld_type_hafez
        ratio = self.fld_ratio
        price_qst = self.fld_price_qst
        if type_hafez == 'ratio':
            self.fld_hafez = (ratio * price_qst)/100