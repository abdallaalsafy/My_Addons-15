from odoo import models, fields, api, _

class cls_sells_goods(models.Model):
    _name = 'mdl_sells_goods'
    _description = 'Table Of All Sells Goods'
    _sql_constraints = [('CheckSellsGoodsCount', 'check (fld_count>0)', 'Goods Count Must Be Above Zero'),
                        ('CheckSellsGoodsPriceBuy', 'check (fld_price_buy>0)', 'Goods Price_Buy Must Be Above Zero'),
                        ('CheckSellsGoodsPriceSell', 'check (fld_price_sell>0)', 'Goods Price_Sell Must Be Above Zero')]


    fld_category_id = fields.Many2one('mdl_categorys', string="Category",)
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods", required=True,
                                   domain="[('fld_category_id', '=?', fld_category_id)]", ondelete='restrict')
    fld_unit_catg_id = fields.Many2one(related="fld_goods_id.fld_unit_id.fld_catg_id", store=True)
    fld_unit_id = fields.Many2one("mdl_units", string='Unit', required=True,
                                  domain="[('fld_catg_id','=',fld_unit_catg_id)]", ondelete='restrict')
    fld_count = fields.Integer(string='Count', default=1)
    fld_count_ref_unit = fields.Float(compute='fnc_get_count_ref_unit', string="Count Ref Unit", store=True, )
    fld_count_store = fields.Float(compute='fnc_get_count_store', string="Count In Store",  store=True)

    fld_price_buy = fields.Float(string='Price Buy',  compute='fnc_compute_prices_unit', store=True, readonly=True)
    fld_price_sell = fields.Float(string='Price Sell',  compute='fnc_compute_prices_unit', store=True, readonly=False)
    fld_clc_sell = fields.Float(string='Calc Sell',  compute='fnc_compute_totals', store=True)
    fld_clc_buy = fields.Float(string='Calc Buy',  compute='fnc_compute_totals', store=True)
    fld_win = fields.Float(string='Winning',  compute='fnc_compute_totals', store=True)

    fld_sells_id = fields.Many2one('mdl_sells', string="Sells ID", required=True, ondelete='cascade')
    fld_store_id = fields.Many2one('mdl_stores', string="Store", required=True, ondelete='restrict')

    # This fields for search in buys return goods
    fld_customer_id = fields.Many2one(related="fld_sells_id.fld_customer_id")
    fld_date = fields.Date(related="fld_sells_id.fld_date")

    # ======================= Computed Fields =======================
    @api.depends('fld_goods_id', 'fld_store_id', 'fld_unit_id')
    def fnc_get_count_store(self):
        """Get current stock count for this goods in store using ORM"""
        for rcrd in self:
            if rcrd.fld_goods_id and rcrd.fld_store_id:
                # Use ORM-based function from goods model
                count_ref = rcrd.fld_goods_id.fnc_get_count_one_goods_in_one_store(rcrd.fld_store_id.id)
                unit_factor = rcrd.fld_unit_id.fld_factor if rcrd.fld_unit_id else 1
                rcrd.fld_count_store = count_ref * unit_factor
            else:
                rcrd.fld_count_store = 0

    @api.depends('fld_unit_id', 'fld_count')
    def fnc_get_count_ref_unit(self):
        """Calculate count in reference unit"""
        for rcrd in self:
            if rcrd.fld_unit_id and rcrd.fld_unit_id.fld_factor:
                rcrd.fld_count_ref_unit = rcrd.fld_count / rcrd.fld_unit_id.fld_factor
            else:
                rcrd.fld_count_ref_unit = 0

    @api.depends('fld_goods_id', 'fld_unit_id')
    def fnc_compute_prices_unit(self):
        """Compute prices based on goods and unit conversion"""
        for rcrd in self:
            if rcrd.fld_goods_id and rcrd.fld_unit_id:
                goods = rcrd.fld_goods_id
                goods_factor = goods.fld_unit_id.fld_factor if goods.fld_unit_id else 1
                unit_factor = rcrd.fld_unit_id.fld_factor
                
                if goods_factor and unit_factor and goods_factor > 0:
                    rcrd.fld_price_buy = (goods.fld_price_buy * goods_factor) / unit_factor
                    rcrd.fld_price_sell = (goods.fld_price_sell * goods_factor) / unit_factor
                else:
                    rcrd.fld_price_buy = 0
                    rcrd.fld_price_sell = 0
            else:
                rcrd.fld_price_buy = 0
                rcrd.fld_price_sell = 0

    @api.depends('fld_count', 'fld_price_buy', 'fld_price_sell')
    def fnc_compute_totals(self):
        """Calculate totals and winning"""
        for rcrd in self:
            clc_buy = rcrd.fld_price_buy * rcrd.fld_count
            clc_sell = rcrd.fld_price_sell * rcrd.fld_count
            win = clc_sell - clc_buy
            rcrd.fld_clc_buy = clc_buy
            rcrd.fld_clc_sell = clc_sell
            rcrd.fld_win = win

    # ======================= Onchange Functions =======================
    @api.onchange('fld_category_id')
    def _onchange_category(self):
        """Clear goods when category changes"""
        if self.fld_category_id and self.fld_goods_id and self.fld_category_id != self.fld_goods_id.fld_category_id:
            self.fld_goods_id = False

    @api.onchange('fld_goods_id')
    def fnc_onchange_goods(self):
        """Set unit and category when goods changes"""
        goods_id = self.fld_goods_id
        if goods_id:
            self.fld_unit_id = goods_id.fld_unit_id
            if goods_id.fld_category_id and goods_id.fld_category_id != self.fld_category_id:
                self.fld_category_id = goods_id.fld_category_id

