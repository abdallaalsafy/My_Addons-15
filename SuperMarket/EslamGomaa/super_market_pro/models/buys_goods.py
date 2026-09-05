from odoo import models, fields, api, _


class cls_buys_goods(models.Model):
    _name = 'mdl_buys_goods'
    _description = 'Table Of All Buys Goods'
    _sql_constraints = [('CheckBuysGoodsCount', 'check (fld_count>0)', 'Goods Count Must Be Above Zero'),
                        ('CheckBuysGoodsPriceBuy', 'check (fld_price_buy>0)', 'Goods Price_Buy Must Be Above Zero'),
                        ('CheckBuysGoodsPriceSell', 'check (fld_price_sell>0)', 'Goods Price_Sell Must Be Above Zero')]


    fld_buys_id = fields.Many2one('mdl_buys', string="Buys ID", required=True, ondelete='cascade')
    fld_vendor_id = fields.Many2one(related="fld_buys_id.fld_vendor_id", store=True)
    fld_date = fields.Date(related="fld_buys_id.fld_date", store=True)
    fld_store_id = fields.Many2one('mdl_stores', string="Store", required=True, ondelete='restrict')
    fld_category_id = fields.Many2one('mdl_categorys', string="Category", ondelete='restrict')
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods", required=True,
                                   domain="[('fld_category_id', '=?', fld_category_id)]",ondelete='restrict')
    fld_unit_catg_id=fields.Many2one(related="fld_goods_id.fld_unit_id.fld_catg_id", store=True)
    fld_unit_id = fields.Many2one("mdl_units",string='Unit', required=True, domain="[('fld_catg_id','=',fld_unit_catg_id)]", ondelete='restrict')

    fld_count = fields.Integer(string='Count', default=1)
    fld_count_ref_unit = fields.Float(compute='fnc_get_count_ref_unit', string="Count Ref Unit", store=True,)
    fld_count_store = fields.Float(compute='fnc_get_count_store', string="Count In Store", store=True)

    fld_price_buy = fields.Float(string='Price Buy', compute='fnc_compute_prices_unit', store=True, readonly=False)
    fld_price_sell = fields.Float(string='Price Sell', readonly=True, compute='fnc_compute_prices_unit', store=True)
    
    # Computed fields for totals
    fld_clc_sell = fields.Float(string='Calc Sell', compute='fnc_compute_totals', store=True)
    fld_clc_buy = fields.Float(string='Calc Buy', compute='fnc_compute_totals', store=True)
    fld_win = fields.Float(string='Winning', compute='fnc_compute_totals', store=True)


    # ======================= Onchange Function =======================
    @api.onchange('fld_category_id')
    def _onchange_category_id(self):
        if self.fld_category_id and self.fld_category_id != self.fld_goods_id.fld_category_id:
            self.fld_goods_id = False

    @api.onchange('fld_goods_id')
    def _onchange_goods_id(self):
        goods_id = self.fld_goods_id
        if goods_id:
            self.fld_unit_id = goods_id.fld_unit_id
            if goods_id.fld_category_id and goods_id.fld_category_id != self.fld_category_id:
                self.fld_category_id = goods_id.fld_category_id

    # ======================= Computed Fields =======================
    @api.depends('fld_goods_id', 'fld_store_id', 'fld_unit_id')
    def fnc_get_count_store(self):
        """Calculate current stock count using ORM-based function"""
        for rcrd in self:
            if not rcrd.fld_goods_id or not rcrd.fld_store_id:
                rcrd.fld_count_store = 0
                continue

            # Get count in reference units using the new ORM function
            count_ref = rcrd.fld_goods_id.fnc_get_count_one_goods_in_one_store(rcrd.fld_store_id.id)

            # Convert to current unit
            unit_factor = rcrd.fld_unit_id.fld_factor or 1.0
            rcrd.fld_count_store = count_ref * unit_factor

    @api.depends('fld_unit_id', 'fld_count')
    def fnc_get_count_ref_unit(self):
        for rcrd in self:
            if rcrd.fld_unit_id:
                rcrd.fld_count_ref_unit = rcrd.fld_count / rcrd.fld_unit_id.fld_factor
            else:
                rcrd.fld_count_ref_unit = 0

    @api.depends('fld_count', 'fld_price_buy', 'fld_price_sell')
    def fnc_compute_totals(self):
        """Compute buy, sell, and win totals"""
        for record in self:
            price_buy = record.fld_price_buy or 0
            price_sell = record.fld_price_sell or 0
            count = record.fld_count or 0

            clc_buy = price_buy * count
            clc_sell = price_sell * count
            win = clc_sell - clc_buy

            record.fld_clc_buy = clc_buy
            record.fld_clc_sell = clc_sell
            record.fld_win = win

    @api.depends('fld_goods_id', 'fld_unit_id')
    def fnc_compute_prices_unit(self):
        """Compute prices based on goods and unit conversion"""
        for record in self:
            goods_id = record.fld_goods_id
            unit_id = record.fld_unit_id

            if goods_id and unit_id:
                goods_factor = goods_id.fld_unit_id.fld_factor
                unit_factor = unit_id.fld_factor

                if goods_factor and unit_factor and goods_factor > 0:
                    price_goods_buy = goods_id.fld_price_buy
                    price_goods_sell = goods_id.fld_price_sell

                    record.fld_price_buy = (price_goods_buy * goods_factor) / unit_factor
                    record.fld_price_sell = (price_goods_sell * goods_factor) / unit_factor
                else:
                    record.fld_price_buy = 0
                    record.fld_price_sell = 0
            else:
                record.fld_price_buy = 0
                record.fld_price_sell = 0

