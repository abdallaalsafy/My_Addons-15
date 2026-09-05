from odoo import models, fields, api
import datetime


class Cls_search_isalls(models.TransientModel):
    _name = 'wzrd_search_isalls'
    _description = 'Wizard Of Search Isalls'

    @api.onchange('fld_region_id')
    def _onchange_region(self):
        if (self.fld_region_id and self.fld_region_id != self.fld_place_id.fld_region_id) or not self.fld_region_id: self.fld_place_id = False

    @api.onchange('fld_place_id')
    def _onchange_place(self):
        if self.fld_place_id.fld_region_id: self.fld_region_id = self.fld_place_id.fld_region_id

    def fnc_get_domain(self):
        domain=[]
        reg_month = self.fld_month
        reg_year = self.fld_year
        date_selct = self.fld_date_selct
        sell = self.fld_sell_id
        mandoop = self.fld_mandoop_id
        collector = self.fld_collector_id
        collector_isall = self.fld_collector_isall_id
        customer = self.fld_customer_id
        phone = self.fld_phone
        region = self.fld_region_id
        place = self.fld_place_id
        paid = self.fld_is_paid
        printed = self.fld_is_printed
        actv = self.fld_active
        frst_reg_isall = self.fld_frst_reg_isall

        if (reg_month or reg_year) and date_selct:
            if date_selct=='this':
                if reg_month:
                    domain = [('fld_month', '=', reg_month)]
                if reg_year:
                    domain += [('fld_year', '=', reg_year)]
            elif date_selct=='oldest':
                if reg_month and not reg_year:
                    domain = [('fld_month', '<=', reg_month)]
                elif reg_month and reg_year:
                    domain = ['|','&',('fld_month', '<=', reg_month),('fld_year', '=', reg_year),('fld_year', '<=', reg_year)]
                elif reg_year and not reg_month:
                    domain = [('fld_year', '<', reg_year)]
            elif date_selct=='newest':
                if reg_month and not reg_year:
                    domain = [('fld_month', '>=', reg_month)]
                elif reg_month and reg_year:
                    domain = ['|', '&', ('fld_month', '>=', reg_month), ('fld_year', '=', reg_year),
                              ('fld_year', '>', reg_year)]
                elif reg_year and not reg_month:
                    domain = [('fld_year', '>=', reg_year)]
        if sell:
            domain += [('fld_sell_id','=',sell.id)]
        if collector_isall:
            domain += [('fld_collector_isall_id','=',collector_isall.id)]
        if paid:
            if paid == 'yes':
                domain += [('fld_is_paid', '=', True)]
            elif paid == 'no':
                domain += [('fld_is_paid', '=', False)]
        if printed:
            if printed == 'yes':
                domain += [('fld_is_printed', '=', True)]
            elif printed == 'no':
                domain += [('fld_is_printed', '=', False)]
        if actv:
            if actv == 'yes':
                domain += [('active', '=', True)]
            elif actv == 'no':
                domain += [('active', '=', False)]
        if mandoop:
            domain += [('fld_mandoops.id','=',mandoop.id)]
        if collector:
            domain += [('fld_collector_id', '=', collector.id)]
        if customer:
            domain += [('fld_customer_id', '=', customer.id)]
        if region:
            domain += [('fld_region_id', '=', region.id)]
        if place:
            domain += [('fld_place_id', '=', place.id)]
        if phone:
            domain += [('phone', '=', phone)]

        # -------------------------------------
        if frst_reg_isall:
            self._cr.execute("""SELECT Min(id) AS Min_id,fld_sell_id FROM mdl_isalls WHERE fld_is_paid=False GROUP BY fld_sell_id""")
            rcrds = self._cr.fetchall()
            ids_frst_reg_lst = [rcrd[0] for rcrd in rcrds]
            if ids_frst_reg_lst:
                ids_domain = self.env['mdl_isalls'].search(domain).ids
                ids_lst = list(set(ids_frst_reg_lst).intersection(set(ids_domain)))
            else:
                ids_lst = []
            domain = [('id', 'in', ids_lst)]
        # ---------------------------------------
        return {'type': 'ir.actions.act_window',
            'name': 'Search Isalls Form',
            'view_type': 'tree',
            'view_mode': 'list',
            'res_model': 'mdl_isalls',
            'domain': domain}

    fld_sell_id = fields.Many2one('mdl_sells', string="Sells ID")
    fld_mandoop_id = fields.Many2one('mdl_mandoops', string="Mandoop Name")
    fld_collector_id = fields.Many2one('mdl_mandoops', string="Collector Name")
    fld_collector_isall_id = fields.Many2one('mdl_mandoops', string="Collector_Isall Name")
    fld_customer_id = fields.Many2one('mdl_customers', string="Customer Name")
    fld_phone = fields.Char(string="Customer Phone")
    fld_region_id = fields.Many2one('mdl_regions', string="Region Name")
    fld_place_id = fields.Many2one('mdl_places', string="Place Name", domain="[('fld_region_id', '=?', fld_region_id)]")
    fld_month = fields.Selection(string="Reg Month", selection=[(str(i), i) for i in range(1, 13)],default=str(datetime.date.today().month))
    fld_year = fields.Selection(string="Reg Year", selection=[(str(i), i) for i in range(2024, 2051)],default=str(datetime.date.today().year))
    fld_date_selct = fields.Selection(string="About Date", selection=[('this','Equal To This Date'),
                                                 ('oldest','Older Than This Date'),
                                                 ('newest','Newest Than This Date')], default='this')
    fld_is_paid = fields.Selection(selection=[('yes','Is Paid'),('no','Not Paid')], string="Is Paid?")
    fld_is_printed = fields.Selection(selection=[('yes','Is Printed'),('no','Not Printed')],string="Is Printed?")
    fld_active = fields.Selection(selection=[('yes','Is Active'),('no','Not Active')],default='yes', string="Active")
    fld_frst_reg_isall = fields.Boolean(string="First Reg Isall")