from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import datetime

class cls_willing(models.TransientModel):
    _name = 'wzrd_willing'
    _description = 'Wizard Of willing'

    @api.onchange('fld_date_f','fld_date_t','fld_date_selc')
    def fnc_calc(self):
        domain=[]
        date_f=self.fld_date_f
        date_t=self.fld_date_t
        date_slc=self.fld_date_selc
        if date_f and date_t:
            domain=[('fld_date','>=',date_f),('fld_date','<=',date_t)]
        elif date_slc:
            domain = [('fld_date', '>=', date_f), ('fld_date', '<=', date_t)]
            if date_slc=='day':
                domain = [('fld_date', '=', fields.Date.today())]
            elif date_slc=='week':
                domain = [('fld_date', '>=', fields.Date.today()+timedelta(weeks=-1))]
            elif date_slc=='month':
                domain = [('fld_date', '>=', fields.Date.today()+relativedelta(months=-1))]
            elif date_slc=='year':
                domain = [('fld_date', '>=', fields.Date.today()+relativedelta(years=-1))]
            elif date_slc=='q1':
                domain = [('fld_date', '>=', datetime.date.today().replace (day=1,month=1,)),
                          ('fld_date', '<=', datetime.date.today().replace (day=31,month=3,))]
            elif date_slc=='q2':
                domain = [('fld_date', '>=', datetime.date.today().replace (day=1,month=4,)),
                          ('fld_date', '<=', datetime.date.today().replace (day=30,month=6,))]
            elif date_slc=='q3':
                domain = [('fld_date', '>=', datetime.date.today().replace (day=1,month=7,)),
                          ('fld_date', '<=', datetime.date.today().replace (day=30,month=9,))]
            elif date_slc=='q4':
                domain = [('fld_date', '>=', datetime.date.today().replace (day=1,month=10,)),
                          ('fld_date', '<=', datetime.date.today().replace (day=31,month=12,))]
        if (date_f and date_t) or date_slc:
            tbl=self.env["mdl_sells"]
            rcrds=tbl.search(domain)
            self.fld_count_sells=len(rcrds)
            self.fld_totals_sells = sum (rcrds.mapped ('fld_total'))
            self.fld_discounts_sells = sum(rcrds.mapped('fld_discount'))
            self.fld_wins_sells = sum(rcrds.mapped('fld_win'))

            tbl = self.env["mdl_sells_r"]
            rcrds = tbl.search(domain)
            self.fld_count_sells_r = len(rcrds)
            self.fld_totals_sells_r = sum(rcrds.mapped('fld_total'))
            self.fld_discounts_sells_r = sum(rcrds.mapped('fld_discount'))

            tbl = self.env["mdl_buys"]
            rcrds = tbl.search(domain)
            self.fld_count_buys = len(rcrds)
            self.fld_totals_buys = sum(rcrds.mapped('fld_total'))
            self.fld_discounts_buys = sum(rcrds.mapped('fld_discount'))

            tbl = self.env["mdl_buys_r"]
            rcrds = tbl.search(domain)
            self.fld_count_buys_r = len(rcrds)
            self.fld_totals_buys_r = sum(rcrds.mapped('fld_total'))
            self.fld_discounts_buys_r = sum(rcrds.mapped('fld_discount'))

            totl_in=0
            totl_out=0
            tbl = self.env["mdl_customers_in"]
            rcrds = tbl.search(domain)
            totl_in += sum(rcrds.mapped('fld_paying'))
            tbl = self.env["mdl_vendors_in"]
            rcrds = tbl.search(domain)
            totl_in += sum(rcrds.mapped('fld_paying'))
            self.fld_in = totl_in

            tbl = self.env["mdl_customers_out"]
            rcrds = tbl.search(domain)
            totl_out += sum(rcrds.mapped('fld_paying'))
            tbl = self.env["mdl_vendors_out"]
            rcrds = tbl.search(domain)
            totl_out += sum(rcrds.mapped('fld_paying'))
            self.fld_out = totl_out

            tbl = self.env["mdl_spending"]
            rcrds = tbl.search(domain)
            self.fld_spending= sum(rcrds.mapped('fld_paying'))


    fld_date_f=fields.Date(string="From")
    fld_date_t = fields.Date(string="To")
    fld_date_selc=fields.Selection([("day","Day"),
                                    ("week","Week"),
                                    ("month","Month"),
                                    ("year","Year"),
                                    ("q1","Q1"),
                                    ("q2","Q2"),
                                    ("q3","Q3"),
                                    ("q4","Q4")],string="Period")

    fld_count_sells=fields.Integer(string="Count Sell",readonly=True)
    fld_totals_sells = fields.Float(string="Totals",readonly=True)
    fld_discounts_sells = fields.Float(string="Discounts",readonly=True)
    fld_wins_sells = fields.Float(string="Wins",readonly=True)

    fld_count_sells_r = fields.Integer(string="Count Sell_r",readonly=True)
    fld_totals_sells_r = fields.Float(string="Totals",readonly=True)
    fld_discounts_sells_r = fields.Float(string="Discounts",readonly=True)

    fld_count_buys = fields.Integer(string="Count Buys",readonly=True)
    fld_totals_buys = fields.Float(string="Totals",readonly=True)
    fld_discounts_buys = fields.Float(string="Discounts",readonly=True)

    fld_count_buys_r = fields.Integer(string="Count Buys_r",readonly=True)
    fld_totals_buys_r = fields.Float(string="Totals",readonly=True)
    fld_discounts_buys_r = fields.Float(string="Discounts",readonly=True)

    fld_in = fields.Float(string="In",readonly=True)
    fld_out = fields.Float(string="Out",readonly=True)
    fld_spending = fields.Float(string="Spending",readonly=True)



