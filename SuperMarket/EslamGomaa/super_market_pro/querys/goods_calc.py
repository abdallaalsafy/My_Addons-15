from odoo import models, fields, api, _
from odoo import tools


class cls_goods_calc(models.Model):
    _name = 'mdl_goods_calc'
    _auto = False
    _description = 'Table Of All Goods Calc'
    _order = "fld_goods_id"

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self.fnc_sql()))

    def fnc_sql(self):
        tbl0 = "SELECT mdl_goods.id,fld_price_buy,fld_price_sell,fld_factor FROM mdl_goods INNER JOIN mdl_units ON mdl_goods.fld_unit_id = mdl_units.id"
        tbl1 = "SELECT fld_goods_id, fld_count_ref_unit FROM mdl_buys_goods"
        tbl2 = "SELECT fld_goods_id, fld_count_ref_unit FROM mdl_sells_r_goods"
        tbl3 = "SELECT fld_goods_id, -fld_count_ref_unit FROM  mdl_sells_goods"
        tbl4 = "SELECT fld_goods_id, -fld_count_ref_unit FROM mdl_buys_r_goods"
        tbl5 = "{} Union All {} Union All {} Union All {}".format(tbl1, tbl2, tbl3, tbl4)
        tbl6 = "Select fld_goods_id,sum(fld_count_ref_unit) As fld_count from ({}) AS tbl00 Group By fld_goods_id".format(tbl5)
        tbl7 = """Select fld_goods_id,fld_price_buy,fld_price_sell,(fld_count * fld_factor) AS fld_count From
                        (({}) AS tbl8 INNER JOIN ({}) AS tbl9 ON tbl8.fld_goods_id = tbl9.id)""".format(tbl6, tbl0)
        return """SELECT row_number() Over (ORDER By 1) As id, fld_goods_id,fld_count,
                  (fld_count * fld_price_buy) as fld_clc_buy,
         (fld_count * fld_price_sell) as fld_clc_sell,
         (fld_count * fld_price_sell)-(fld_count * fld_price_buy) as fld_win
        From({}) AS tblx Where fld_count<>0""".format(tbl7)

    fld_category_id = fields.Many2one(related='fld_goods_id.fld_category_id')
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods")
    fld_unit_id = fields.Many2one(related='fld_goods_id.fld_unit_id')
    fld_price_buy = fields.Float(related='fld_goods_id.fld_price_buy')
    fld_price_sell = fields.Float(related='fld_goods_id.fld_price_sell')

    fld_clc_sell = fields.Float(string='Calc Sell', )
    fld_clc_buy = fields.Float(string='Calc Buy', )
    fld_win = fields.Float(string='Winning', )

    fld_count = fields.Float(string='Count', digit=0)

