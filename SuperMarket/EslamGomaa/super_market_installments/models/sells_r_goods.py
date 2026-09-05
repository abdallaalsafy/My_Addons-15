from odoo import models, fields, api, _

class cls_sells_r_goods(models.Model):
    _inherit = 'mdl_sells_r_goods'
    _sql_constraints = [('CheckReturnSellsGoodsPriceQest', 'check (fld_price_qst>0)', 'Goods Price_Qest Must Be Above Zero')]


    fld_is_qst = fields.Boolean(related="fld_sells_r_id.fld_parent_id.fld_is_qst")
    # Calculated Fields
    fld_price_qst = fields.Float(string='Price Qest', compute='fnc_compute_qest_r_prices_unit', store=True,
                                 readonly=False)
    fld_hafez = fields.Float(string='Hafez', compute='fnc_compute_qest_r_prices_unit', store=True, readonly=False)

    fld_clc_qst = fields.Float(string='Calc Qest', compute='fnc_compute_qest_r_totals', store=True)
    fld_win_qst = fields.Float(string='Winning Qest', compute='fnc_compute_qest_r_totals', store=True)
    fld_clc_hafez = fields.Float(string='Calc Hafez', compute='fnc_compute_qest_r_totals', store=True)


    @api.depends('fld_goods_id', 'fld_unit_id')
    def fnc_compute_qest_r_prices_unit(self):
        """Compute prices based on goods and unit conversion"""
        for rcrd in self:
            if rcrd.fld_goods_id and rcrd.fld_unit_id:
                goods = rcrd.fld_goods_id
                goods_factor = goods.fld_unit_id.fld_factor if goods.fld_unit_id else 1
                unit_factor = rcrd.fld_unit_id.fld_factor

                if goods_factor and unit_factor and goods_factor > 0:
                    rcrd.fld_price_qst = (goods.fld_price_qst * goods_factor) / unit_factor
                    rcrd.fld_hafez = (goods.fld_hafez * goods_factor) / unit_factor
                else:
                    rcrd.fld_price_qst = 0
                    rcrd.fld_hafez = 0
            else:
                rcrd.fld_price_qst = 0
                rcrd.fld_hafez = 0

    @api.depends('fld_count', 'fld_price_qst', 'fld_hafez', 'fld_clc_buy')
    def fnc_compute_qest_r_totals(self):
        """Calculate totals and winning"""
        for rcrd in self:
            clc_buy = rcrd.fld_clc_buy
            clc_hafz = rcrd.fld_hafez * rcrd.fld_count
            clc_qst = rcrd.fld_price_qst * rcrd.fld_count
            win = clc_qst - clc_buy

            rcrd.fld_clc_hafez = clc_hafz
            rcrd.fld_clc_qst = clc_qst
            rcrd.fld_win_qst = win

