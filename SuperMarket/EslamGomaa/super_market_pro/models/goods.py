from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..mine_3 import cls_sqls

class cls_goods(models.Model):
    _name = 'mdl_goods'
    _description = 'Table Of All Goods'
    _order = "name"
    _sql_constraints = [('uniqueGoodsName', 'unique(name)', 'The Goods Is Existe Before'),
                        ('CheckGoodsPriceBuy', 'check (fld_price_buy>0)', 'Price_Buy Must Be Above Zero'),
                        ('CheckGoodsPriceSell', 'check (fld_price_sell>0)', 'Price_Sell Must Be Above Zero')]

    def _default_unit_id(self):
        """Get default unit: prefer reference unit, fallback to any unit."""
        unit =  self.env.ref('super_market_pro.unit_default_ref')
        if unit:
            return unit.id



    name = fields.Char(string='Name', required=True, index=True)
    fld_category_id = fields.Many2one('mdl_categorys', string="Category", store=True, ondelete='restrict')
    fld_unit_id = fields.Many2one("mdl_units", string='Unit', default=_default_unit_id, required=True, ondelete='restrict',)
    fld_price_buy = fields.Float(string='Price Buy', required=True, )
    fld_price_sell = fields.Float(string='Price Sell', required=True, )
    fld_alarms = fields.Integer(string='Alarms', default=1)
    fld_description = fields.Text(string='Description')
    fld_notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    fld_img = fields.Image(max_width=200, max_height=200)


    # ======================= Built-in Methods =======================
    def write(self, vals):
        new_unit_id = vals.get('fld_unit_id')
        if new_unit_id:
            old_ctg_unit_id = self.fld_unit_id.fld_catg_id
            new_unit_ctg_id = self.env['mdl_units'].browse(new_unit_id).fld_catg_id
            is_used = self.fnc_check_goods_usage()
            if (old_ctg_unit_id != new_unit_ctg_id) and is_used:
                raise UserError(_('The Goods is Used , Can Not Change Its Unit!'))
        rtn = super(cls_goods, self).write(vals)
        return rtn

    # ======================= Business Methods =======================
    def fnc_get_count_one_goods_in_one_store(self, store_id):
        """
        Get count of current goods in specific store using ORM
        Returns the quantity in reference units
        Implements the same logic as the SQL query using ORM aggregation
        """
        domain = [('fld_goods_id', '=', self.id), ('fld_store_id', '=', store_id)]
        if not self or not store_id:
            return 0
        
        try:
            # Implement the SQL logic using ORM with aggregation
            # Buys (positive)
            buys_goods = self.env['mdl_buys_goods'].search(domain)
            buys_total = sum(buys.fld_count_ref_unit for buys in buys_goods if buys.fld_count_ref_unit)
            
            # Returns Buys (negative)
            buys_r_goods = self.env['mdl_buys_r_goods'].search(domain)
            buys_r_total = sum(buys_r.fld_count_ref_unit for buys_r in buys_r_goods if buys_r.fld_count_ref_unit)
            
            # Sells (negative)
            sells_goods = self.env['mdl_sells_goods'].search(domain)
            sells_total = sum(sells.fld_count_ref_unit for sells in sells_goods if sells.fld_count_ref_unit)
            
            # Returns Sells (positive)
            sells_r_goods = self.env['mdl_sells_r_goods'].search(domain)
            sells_r_total = sum(sells_r.fld_count_ref_unit for sells_r in sells_r_goods if sells_r.fld_count_ref_unit)
            
            # Charges (from store_f_id - negative, to store_t_id - positive)
            charges_goods_from = self.env['mdl_charges_goods'].search([
                ('fld_goods_id', '=', self.id),
                ('fld_store_f_id', '=', store_id)
            ])
            charges_from_total = sum(charges.fld_count_ref_unit for charges in charges_goods_from if charges.fld_count_ref_unit)
            
            charges_goods_to = self.env['mdl_charges_goods'].search([
                ('fld_goods_id', '=', self.id),
                ('fld_store_t_id', '=', store_id)
            ])
            charges_to_total = sum(charges.fld_count_ref_unit for charges in charges_goods_to if charges.fld_count_ref_unit)
            
            # Calculate final total like the SQL query
            final_total = buys_total - buys_r_total - sells_total + sells_r_total - charges_from_total + charges_to_total
            
            return final_total if final_total > 0 else 0
                
        except Exception as e:
            return 0

    def fnc_check_goods_usage(self):
        """Check if goods are used in related models"""
        models_to_check = [
            'mdl_buys_goods',
            'mdl_buys_r_goods',
            'mdl_sells_goods',
            'mdl_sells_r_goods',
            'mdl_charges_goods'
        ]
        for model_name in models_to_check:
            try:
                model = self.env[model_name]
                used_records = model.search([('fld_goods_id', '=', self.id)], limit=1)
                if used_records:
                    return True
            except KeyError:
                continue

        return False
