from odoo import models, fields, api, _
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class Cls_search_buys_goods(models.TransientModel):
    _name = 'wzrd_search_buys_goods'
    _description = 'Wizard Of Search Buys Goods'



    # Transaction type selection
    fld_transaction_type = fields.Selection([
        ('buys', _('Purchases')),
        ('buys_r', _('Purchase Returns')),
        ('sells', _('Sales')),
        ('sells_r', _('Sales Returns')),
    ], string=_("Transaction Type"), default='buys', required=True)

    # Existing fields
    fld_customer_id = fields.Many2one("mdl_customers", string="Customer")
    fld_vendor_id = fields.Many2one("mdl_vendors", string="Vendor")
    fld_category_id = fields.Many2one('mdl_categorys', string=_("Category"))
    fld_goods_id = fields.Many2one('mdl_goods', string=_("Goods"), domain="[('fld_category_id', '=?', fld_category_id)]")

    fld_date_f = fields.Date(string=_("From"))
    fld_date_t = fields.Date(string=_("To"))
    fld_date_selc = fields.Selection([("day", _("Day")),
                                      ("week", _("Week")),
                                      ("month", _("Month")),
                                      ("year", _("Year")),
                                      ("q1", _("Q1")),
                                      ("q2", _("Q2")),
                                      ("q3", _("Q3")),
                                      ("q4", _("Q4"))], string=_("Period"))

    def fnc_get_domain(self):
        """Build domain based on transaction type and filters"""
        domain = []
        date_f = self.fld_date_f
        date_t = self.fld_date_t
        date_slc = self.fld_date_selc
        transaction_type = self.fld_transaction_type
        customer = self.fld_customer_id.id
        vendor = self.fld_vendor_id.id
        goods = self.fld_goods_id.id
        catg_goods = self.fld_category_id.id
        
        # Date filtering
        if date_f and date_t:
            domain = [('fld_date', '>=', date_f), ('fld_date', '<=', date_t)]
        elif date_slc:
            if date_slc == 'day':
                domain = [('fld_date', '=', fields.Date.today())]
            elif date_slc == 'week':
                domain = [('fld_date', '>=', fields.Date.today() + timedelta(weeks=-1))]
            elif date_slc == 'month':
                domain = [('fld_date', '>=', fields.Date.today() + relativedelta(months=-1))]
            elif date_slc == 'year':
                domain = [('fld_date', '>=', fields.Date.today() + relativedelta(years=-1))]
            elif date_slc == 'q1':
                current_year = date.today().year
                domain = [('fld_date', '>=', date(current_year, 1, 1)),
                          ('fld_date', '<=', date(current_year, 3, 31))]
            elif date_slc == 'q2':
                current_year = date.today().year
                domain = [('fld_date', '>=', date(current_year, 4, 1)),
                          ('fld_date', '<=', date(current_year, 6, 30))]
            elif date_slc == 'q3':
                current_year = date.today().year
                domain = [('fld_date', '>=', date(current_year, 7, 1)),
                          ('fld_date', '<=', date(current_year, 9, 30))]
            elif date_slc == 'q4':
                current_year = date.today().year
                domain = [('fld_date', '>=', date(current_year, 10, 1)),
                          ('fld_date', '<=', date(current_year, 12, 31))]
        
        # vendor and customer filtering based on transaction type
        if transaction_type in ['buys', 'buys_r'] and vendor > 0:
            domain += [('fld_vendor_id', '=', vendor)]
        elif transaction_type in ['sells', 'sells_r'] and customer > 0:
            domain += [('fld_customer_id', '=', customer)]
        
        # Goods and category filtering (only for goods transactions)
        if goods:
            domain += [('fld_goods_id', '=', goods)]
        if catg_goods:
            domain += [('fld_category_id', '=', catg_goods)]

        return domain

    def fnc_do_action(self):
        """Execute search action based on transaction type"""
        transaction_type = self.fld_transaction_type
        
        # Define model and view mappings
        model_view_mapping = {
            'buys': ('mdl_buys_goods', 'search_buys_goods_list_id'),
            'buys_r': ('mdl_buys_r_goods', 'search_buys_r_goods_list_id'),
            'sells': ('mdl_sells_goods', 'search_sells_goods_list_id'),
            'sells_r': ('mdl_sells_r_goods', 'search_sells_r_goods_list_id'),
        }
        
        # Get appropriate model and view
        res_model, view_ref = model_view_mapping.get(transaction_type, ('mdl_buys_goods', 'search_buys_goods_list_id'))
        
        # Try to get the view ID, fallback to default if not found
        try:
            view_id = self.env.ref('super_market_pro.%s' % view_ref).id
        except ValueError:
            view_id = False
        
        # Set action name based on transaction type
        action_names = {
            'buys': _('Search Purchases Goods'),
            'buys_r': _('Search Purchase Returns Goods'),
            'sells': _('Search Sales Goods'),
            'sells_r': _('Search Sales Returns Goods'),
        }
        
        action_name = action_names.get(transaction_type, _('Search Results'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': action_name,
            'view_type': 'tree',
            'view_mode': 'list',
            'res_model': res_model,
            'view_id': view_id,
            'domain': self.fnc_get_domain(),
            'target': 'current',
        }

    @api.onchange('fld_category_id')
    def _onchange_category(self):
        if self.fld_category_id and self.fld_goods_id and self.fld_category_id != self.fld_goods_id.fld_category_id:
            self.fld_goods_id = False

    @api.onchange('fld_transaction_type')
    def _onchange_transaction_type(self):
        """Change customer and vendor field based on transaction type"""
        if self.fld_transaction_type in ['buys', 'buys_r']:
            self.fld_customer_id = False
            # Update field definition to vendor
        elif self.fld_transaction_type in ['sells', 'sells_r']:
            self.fld_vendor_id = False
            # Update field definition to customer

    @api.onchange('fld_goods_id')
    def _onchange_goods(self):
        if self.fld_goods_id:
            if self.fld_goods_id.fld_category_id:
                self.fld_category_id = self.fld_goods_id.fld_category_id