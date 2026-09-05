from odoo import models, fields, api
from odoo import tools
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import datetime

class Cls_search_mandoops_sells(models.TransientModel):
    _name = 'wzrd_search_mandoops_sells'
    _description = 'Wizard Of Search Mandoops Sells'

    def inits(self):
        tools.drop_view_if_exists(self.env.cr, 'mdl_mandoops_sells')
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % ('mdl_mandoops_sells', self.fnc_sql()))

    def fnc_sql(self):
        tbl1 = """(Select Count(mdl_sells_id) As fld_count_mandoops, mdl_sells_id
             From mdl_mandoops_mdl_sells_rel Group By mdl_sells_id) As tbl1 """
        tbl2 = """(Select mdl_sells_id,fld_is_qst,
                (fld_total_qst/fld_count_mandoops) AS fld_total_qst,
                (fld_win_qst/fld_count_mandoops) AS fld_win_qst,
                (fld_total_hafez/fld_count_mandoops) AS fld_total_hafez,
                (fld_total/fld_count_mandoops) AS fld_total,
                (fld_win/fld_count_mandoops) AS fld_win
              From {} INNER JOIN mdl_sells ON tbl1.mdl_sells_id=mdl_sells.id {} ) As tbl2 """.format(tbl1,self.fnc_get_where())
        tblr2 = """(Select mdl_sells_id,fld_is_qst,
                        (fld_total_qst/fld_count_mandoops) AS fld_total_qst,
                        (fld_win_qst/fld_count_mandoops) AS fld_win_qst,
                        (fld_total_hafez/fld_count_mandoops) AS fld_total_hafez,
                        (fld_total/fld_count_mandoops) AS fld_total,
                        (fld_win/fld_count_mandoops) AS fld_win
                      From {} INNER JOIN mdl_sells_r ON tbl1.mdl_sells_id=mdl_sells_r.fld_parent_id {} ) As tblr2 """.format(tbl1,self.fnc_get_where())
        tbl3 = """Select mdl_mandoops_id,
                0 As fld_count_cash_r,
                0 As fld_count_qst_r,
                Count(mdl_mandoops_id) As fld_count_cash,
                0 As fld_count_qst,
                0 AS fld_total_qst,
                0 AS fld_win_qst,
                Sum(fld_total_hafez) AS fld_total_hafez,
                Sum(fld_total) As fld_total,
                Sum(fld_win) As fld_win
                From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                ON tbl2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                WHERE fld_is_qst=False
                Group By mdl_mandoops_id,fld_total_qst,fld_win_qst,fld_count_qst,fld_count_qst_r,fld_count_cash_r""".format(tbl2)
        tblr3 = """Select mdl_mandoops_id,
                    Count(mdl_mandoops_id) As fld_count_cash_r,
                    0 As fld_count_qst_r,
                    0 As fld_count_cash,
                    0 As fld_count_qst,
                    0 AS fld_total_qst,
                    0 AS fld_win_qst,
                    Sum(-fld_total_hafez) AS fld_total_hafez,
                    Sum(-fld_total) As fld_total,
                    Sum(-fld_win) As fld_win
                    From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                    ON tblr2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                    WHERE fld_is_qst=False
                    Group By mdl_mandoops_id,fld_total_qst,fld_win_qst,fld_count_qst,fld_count_cash,fld_count_qst_r""".format(tblr2)
        tbl4 = """Select mdl_mandoops_id,
                    0 As fld_count_cash_r,
                    0 As fld_count_qst_r,
                    0 As fld_count_cash,
                    Count(mdl_mandoops_id) As fld_count_qst,
                    Sum(fld_total_qst) As fld_total_qst,
                    Sum(fld_win_qst) As fld_win_qst,
                    Sum(fld_total_hafez) As fld_total_hafez,
                    0 AS fld_total,
                    0 AS fld_win
                    From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                    ON tbl2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                    WHERE fld_is_qst=True
                    Group By mdl_mandoops_id,fld_total,fld_win,fld_count_cash,fld_count_cash_r,fld_count_qst_r""".format(tbl2)
        tblr4 = """Select mdl_mandoops_id,
                    0 As fld_count_cash_r,
                    Count(mdl_mandoops_id) As fld_count_qst_r,
                    0 As fld_count_cash,
                    0 As fld_count_qst,
                    Sum(-fld_total_qst) As fld_total_qst,
                    Sum(-fld_win_qst) As fld_win_qst,
                    Sum(-fld_total_hafez) As fld_total_hafez,
                    0 AS fld_total,
                    0 AS fld_win
                    From {} INNER JOIN mdl_mandoops_mdl_sells_rel 
                    ON tblr2.mdl_sells_id = mdl_mandoops_mdl_sells_rel.mdl_sells_id
                    WHERE fld_is_qst=True
                    Group By mdl_mandoops_id,fld_total,fld_win,fld_count_cash,fld_count_qst,fld_count_cash_r""".format(tblr2)

        tbl5 = "({} Union All {} Union All {} Union All {}) AS tbl5".format(tbl3, tbl4,tblr3,tblr4)
        tbl6 = """(Select mdl_mandoops_id,
                fld_count_cash_r,
                fld_count_qst_r,
                fld_count_cash,
                fld_count_qst,
                fld_total_qst,
                fld_win_qst,
                fld_total_hafez,
                fld_total,
                fld_win
                From {}) As tbl6""".format(tbl5)

        sql= """
        SELECT row_number() Over (ORDER By 1) As id, mdl_mandoops_id,
        Sum(fld_count_cash_r) AS fld_count_cash_r,
        Sum(fld_count_qst_r) AS fld_count_qst_r,
        Sum(fld_count_cash) AS fld_count_cash,
        Sum(fld_count_qst) AS fld_count_qst,
        Sum(fld_total_qst) As fld_total_qst,
        Sum(fld_win_qst) As fld_win_qst,
        Sum(fld_total_hafez) As fld_total_hafez,
        Sum(fld_total) As fld_total,
        Sum(fld_win) As fld_win,
        (Sum(fld_count_cash)+Sum(fld_count_qst)) As fld_count_sells,
        (Sum(fld_count_cash_r)+Sum(fld_count_qst_r)) As fld_count_sells_r,
        (Sum(fld_total_qst)+Sum(fld_total)) As fld_total_sells,
        (Sum(fld_win_qst)+Sum(fld_win)) As fld_total_winning
        From {}
        Group By mdl_mandoops_id
        """.format(tbl6)
        return sql
    def fnc_get_where(self):
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

    def fnc_do_action(self):
        self.inits()
        return {'type': 'ir.actions.act_window',
            'name': 'Search Mandoops Sells Form',
            'view_type': 'tree',
            'view_mode': 'list',
            'res_model': 'mdl_mandoops_sells'}

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