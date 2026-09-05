from odoo import models, fields, api
from odoo import tools
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class Cls_search_mandoops_goods(models.TransientModel):
    _name = 'wzrd_search_mandoops_goods'
    _description = 'Wizard Of Search Mandoops Goods'

    def inits(self):
        tools.drop_view_if_exists(self.env.cr, 'mdl_mandoops_goods')
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % ('mdl_mandoops_goods', self.fnc_sql()))

    def fnc_sql(self):
        # استعلام جدول البيع مع جدول منتجات البيع
        tbl0 = """(Select fld_sells_id,fld_is_qst,fld_date,
                fld_goods_id,fld_count_ref_unit,
                fld_clc_sell,fld_clc_qst,fld_clc_hafez,mdl_sells_goods.fld_win
              From mdl_sells INNER JOIN mdl_sells_goods ON mdl_sells.id=mdl_sells_goods.fld_sells_id {} ) As tbl0 """.format(self.fnc_get_where_date())
        # أستعلام جدول مرتجع البيع مع جدول منتجات مرتجع البيع
        tblr0 = """(Select fld_parent_id,fld_is_qst,fld_date,
                fld_goods_id,fld_count_ref_unit,
                fld_clc_sell,fld_clc_qst,fld_clc_hafez,mdl_sells_r_goods.fld_win
              From mdl_sells_r INNER JOIN mdl_sells_r_goods ON mdl_sells_r.id=mdl_sells_r_goods.fld_sells_r_id {} ) As tblr0 """.format(
            self.fnc_get_where_date())
        # تجميع جدول مناديب البيع لينتج عدد المناديب لكل فاتورة بيع لها مناديب
        tbl1 = """(Select Count(mdl_sells_id) As fld_count_mandoops, mdl_sells_id
             From mdl_mandoops_mdl_sells_rel Group By mdl_sells_id) As tbl1 """
        # استعلام بين جدول (tbl0) وجدول (tbl1) لنحصل على منتج البيعة وعدد المناديب المشتركين للبيعة
        tbl2 = """(Select mdl_sells_id,fld_is_qst,
                fld_goods_id,
                (fld_count_ref_unit/fld_count_mandoops) AS fld_count_ref_unit,
                (fld_clc_sell/fld_count_mandoops) AS fld_total_sell_mandoop,
                (fld_clc_qst/fld_count_mandoops) AS fld_total_qst_mandoop,
                (fld_clc_hafez/fld_count_mandoops) AS fld_total_hafez_mandoop,
                (fld_win/fld_count_mandoops) AS fld_win_mandoop
              From {} INNER JOIN {} ON tbl0.fld_sells_id=tbl1.mdl_sells_id) As tbl2 """.format(tbl0,tbl1)
        # استعلام بين جدول (tblr0) وجدول (tbl1) لنحصل على منتج مرتجع البيعة وعدد المناديب المشتركين للبيعة
        tblr2 = """(Select mdl_sells_id,fld_is_qst,
                fld_goods_id,
                (fld_count_ref_unit/fld_count_mandoops) AS fld_count_ref_unit,
                (fld_clc_sell/fld_count_mandoops) AS fld_total_sell_mandoop,
                (fld_clc_qst/fld_count_mandoops) AS fld_total_qst_mandoop,
                (fld_clc_hafez/fld_count_mandoops) AS fld_total_hafez_mandoop,
                (fld_win/fld_count_mandoops) AS fld_win_mandoop
              From {} INNER JOIN {} ON tblr0.fld_parent_id=tbl1.mdl_sells_id) As tblr2 """.format(tblr0,tbl1)
        # هذا الأستعلام لفصل منتجات البيع الكاش فقط من منتجات البيع عامة وربطه مع جدول مناديب البيع لنحصل على اسم المندوب
        # ونستبعد البيع الذى ليس له مناديب
        tbl3 = """Select mdl_mandoops_id,
                fld_goods_id,
                SUM(fld_count_ref_unit) AS fld_count_ref_unit,
                Sum(fld_total_sell_mandoop) AS fld_total_sell_mandoop,
                0 AS fld_total_qst_mandoop,
                Sum(fld_total_hafez_mandoop) AS fld_total_hafez_mandoop,
                Sum(fld_win_mandoop) AS fld_win_mandoop
                From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                ON tbl2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                WHERE fld_is_qst=False
                Group By mdl_mandoops_id,fld_goods_id""".format(tbl2)
        # هذا الأستعلام لفصل منتجات مرتجع البيع الكاش فقط من منتجات البيع عامة وربطه مع جدول مناديب مرتجع البيع لنحصل على اسم المندوب
        # ونستبعد مرتجع البيع الذى ليس له مناديب
        tblr3 = """Select mdl_mandoops_id,
                fld_goods_id,
                SUM(-fld_count_ref_unit) AS fld_count_ref_unit,
                Sum(-fld_total_sell_mandoop) AS fld_total_sell_mandoop,
                0 AS fld_total_qst_mandoop,
                Sum(-fld_total_hafez_mandoop) AS fld_total_hafez_mandoop,
                Sum(-fld_win_mandoop) AS fld_win_mandoop
                From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                ON tblr2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                WHERE fld_is_qst=False
                Group By mdl_mandoops_id,fld_goods_id""".format(tblr2)
        # هذا الأستعلام لفصل منتجات البيع القسط فقط من منتجات البيع عامة وربطه مع جدول مناديب البيع لنحصل على اسم المندوب
        # ونستبعد البيع الذى ليس له مناديب
        tbl4 = """Select mdl_mandoops_id,
                fld_goods_id,
                SUM(fld_count_ref_unit) AS fld_count_ref_unit,
                0 AS fld_total_sell_mandoop,
                Sum(fld_total_qst_mandoop) AS fld_total_qst_mandoop,
                Sum(fld_total_hafez_mandoop) AS fld_total_hafez_mandoop,
                Sum(fld_win_mandoop) AS fld_win_mandoop
                From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                ON tbl2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                WHERE fld_is_qst=True
                Group By mdl_mandoops_id,fld_goods_id""".format(tbl2)
        # هذا الأستعلام لفصل منتجات مرتجع البيع القسط فقط من منتجات مرتجع البيع عامة وربطه مع جدول مناديب مرتجع البيع لنحصل على اسم المندوب
        # ونستبعد مرتجع البيع الذى ليس له مناديب
        tblr4 = """Select mdl_mandoops_id,
                fld_goods_id,
                SUM(-fld_count_ref_unit) AS fld_count_ref_unit,
                0 AS fld_total_sell_mandoop,
                Sum(-fld_total_qst_mandoop) AS fld_total_qst_mandoop,
                Sum(-fld_total_hafez_mandoop) AS fld_total_hafez_mandoop,
                Sum(-fld_win_mandoop) AS fld_win_mandoop
                From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                ON tblr2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                WHERE fld_is_qst=True
                Group By mdl_mandoops_id,fld_goods_id""".format(tblr2)
        tbl5 = "({} Union All {} Union All {} Union All {}) AS tbl5".format(tbl3, tbl4,tblr3,tblr4)
        tbl6 = """(Select mdl_mandoops_id,
                fld_goods_id,fld_count_ref_unit,
                fld_total_sell_mandoop,
                fld_total_qst_mandoop,
                fld_total_hafez_mandoop,
                fld_win_mandoop
                From {} ) As tbl6""".format(tbl5)

        tbl7= """
        (SELECT mdl_mandoops_id,fld_goods_id,
        Sum(fld_count_ref_unit) AS fld_count_ref_unit,
        Sum(fld_total_sell_mandoop) AS fld_total_sell_mandoop,
        Sum(fld_total_qst_mandoop) AS fld_total_qst_mandoop,
        Sum(fld_total_hafez_mandoop) AS fld_total_hafez_mandoop,
        Sum(fld_win_mandoop) AS fld_win_mandoop,
        (Sum(fld_total_sell_mandoop)+Sum(fld_total_qst_mandoop)) As fld_total_sells
        From {}
        Group By mdl_mandoops_id,fld_goods_id) As tbl7 """.format(tbl6)

        tbl8 = "(SELECT mdl_goods.id,fld_category_id,fld_factor FROM mdl_goods INNER JOIN mdl_units ON mdl_goods.fld_unit_id = mdl_units.id) As tbl8"

        sql="""Select row_number() Over (ORDER By 1) As id,
            mdl_mandoops_id,fld_goods_id,
            (fld_count_ref_unit * fld_factor) AS fld_count,
            fld_total_sell_mandoop,
            fld_total_qst_mandoop,
            fld_total_hafez_mandoop,
            fld_total_sells,
            fld_win_mandoop
            From {} INNER JOIN {} ON tbl7.fld_goods_id = tbl8.id 
            {} """.format(tbl7,tbl8,self.fnc_get_where_other())
        return sql

    def fnc_get_where_date(self):
        where = ''
        date_f = self.fld_date_f
        date_t = self.fld_date_t
        date_slc = self.fld_date_selc
        if date_f and date_t:
            where = "fld_date >='" + str(date_f) + "' And fld_date <='" + str(date_t) + "'"
        elif date_slc:
            if date_slc == 'day':
                where ="fld_date='" + str(fields.Date.today()) + "'"
            elif date_slc == 'week':
                where = "fld_date >='" + str(fields.Date.today() + timedelta(weeks=-1)) + "'"
            elif date_slc == 'month':
                where = "fld_date >='" + str(fields.Date.today() + relativedelta(months=-1)) + "'"
            elif date_slc == 'year':
                where = "fld_date >='" + str(fields.Date.today() + relativedelta(years=-1)) + "'"
            elif date_slc == 'q1':
                where = "fld_date >='" + str(fields.Date.today().replace(day=1, month=1,)) + \
                        "' And fld_date <='" + str(fields.Date.today().replace(day=31, month=3,)) + "'"
            elif date_slc == 'q2':
                where = "fld_date >='" + str(fields.Date.today().replace(day=1, month=4, )) + \
                        "' And fld_date <='" + str(fields.Date.today().replace(day=30, month=6, )) + "'"
            elif date_slc == 'q3':
                where = "fld_date >='" + str(fields.Date.today().replace(day=1, month=7, )) + \
                        "' And fld_date <='" + str(fields.Date.today().replace(day=30, month=9, )) + "'"
            elif date_slc == 'q4':
                where = "fld_date >='" + str(fields.Date.today().replace(day=1, month=10, )) + \
                        "' And fld_date <='" + str(fields.Date.today().replace(day=31, month=12, )) + "'"
        if where:
            return 'WHERE ' + where
        return where

    def fnc_get_where_other(self):
        where = ''
        mandoop = self.fld_mandoops_id.id
        goods = self.fld_goods_id.id
        catg_goods = self.fld_category_id.id
        if mandoop:
            where = "mdl_mandoops_id ='" + str(mandoop) + "'"
        if goods:
            if where:
                where += " And "
            where += "fld_goods_id ='" + str(goods) + "'"
        if catg_goods:
            if where:
                where += " And "
            where += "fld_category_id ='" + str(catg_goods) + "'"
        if where:
            return 'WHERE ' + where
        return where

    def fnc_do_action(self):
        self.inits()
        return {'type': 'ir.actions.act_window',
            'name': 'Search Mandoops Goods Form',
            'view_type': 'tree',
            'view_mode': 'list',
            'res_model': 'mdl_mandoops_goods'}

    @api.onchange('fld_category_id')
    def _onchange_category(self):
        if self.fld_category_id and self.fld_category_id != self.fld_goods_id.fld_category_id: self.fld_goods_id = False

    @api.onchange('fld_goods_id')
    def fnc_a_goods(self):
        goods_id = self.fld_goods_id
        if goods_id.fld_category_id: self.fld_category_id = goods_id.fld_category_id

    fld_mandoops_id = fields.Many2one("mdl_mandoops", string="Mandoop")
    fld_category_id = fields.Many2one('mdl_categorys', string="Category")
    fld_goods_id = fields.Many2one('mdl_goods', string="Goods",domain="[('fld_category_id', '=?', fld_category_id)]")

    fld_date_f = fields.Date(string="From")
    fld_date_t = fields.Date(string="To")
    fld_date_selc = fields.Selection([("day", "Day"),
                                      ("week", "Week"),
                                      ("month", "Month"),
                                      ("year", "Year"),
                                      ("q1", "Q1"),
                                      ("q2", "Q2"),
                                      ("q3", "Q3"),
                                      ("q4", "Q4")], string="Period")