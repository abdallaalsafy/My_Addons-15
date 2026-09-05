from odoo import models, fields, api, _

class cls_charges_goods(models.Model):
    _name = 'mdl_charges_goods'
    _description = 'Table Of All Charges Goods'
    _order = "fld_goods_id"
    _sql_constraints = [('CheckChargesGoodsCount', 'check (fld_count>0)', 'Goods Count Must Be Above Zero')]

    fld_category_id = fields.Many2one('mdl_categorys', string="Category", store=True)
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods", required=True,
                                   domain="[('fld_category_id', '=?', fld_category_id)]", ondelete='restrict')
    fld_unit_catg_id = fields.Many2one(related="fld_goods_id.fld_unit_id.fld_catg_id", store=True)
    fld_unit_id = fields.Many2one("mdl_units", string='Unit', required=True,
                                  domain="[('fld_catg_id','=',fld_unit_catg_id)]", ondelete='restrict')
    fld_count = fields.Integer(string='Count', default=1)
    fld_count_ref_unit = fields.Float(compute='fnc_get_count_ref_unit', string="Count Ref Unit", store=True, )
    fld_count_store = fields.Float(compute='fnc_get_count_store', string="Count In Store",  store=True)

    # Related fields from charges
    fld_store_f_id = fields.Many2one(related='fld_charges_id.fld_store_f_id', store=True, ondelete='restrict')
    fld_store_t_id = fields.Many2one(related='fld_charges_id.fld_store_t_id', store=True, ondelete='restrict')
    fld_charges_id = fields.Many2one('mdl_charges', string="Charges ID", required=True, ondelete='cascade')


    # ======================= Computed Fields =======================
    @api.depends('fld_goods_id', 'fld_store_f_id', 'fld_unit_id')
    def fnc_get_count_store(self):
        """Get current stock count for this goods in from store using ORM"""
        for rcrd in self:
            if rcrd.fld_goods_id and rcrd.fld_store_f_id:
                # Use ORM-based function from goods model
                count_ref = rcrd.fld_goods_id.fnc_get_count_one_goods_in_one_store(rcrd.fld_store_f_id.id)
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