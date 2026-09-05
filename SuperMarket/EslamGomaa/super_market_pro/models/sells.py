from odoo import models, fields, api, _
from odoo.exceptions import UserError

class cls_sells(models.Model):
    _name = 'mdl_sells'
    _description = 'Table Of All Sells'
    _order = "id desc"

    name = fields.Char(string="Code", default=lambda self: _('New'))
    fld_ref = fields.Char(string="Reference")
    fld_date = fields.Date(string='Date', required=True, )
    fld_notes = fields.Text(string='Notes')

    fld_store_id = fields.Many2one('mdl_stores', string="Store", ondelete='restrict')
    fld_customer_id = fields.Many2one('mdl_customers', string="Customer", ondelete='restrict')

    # Payment fields
    fld_paying = fields.Float(string='Paying', )
    fld_discount = fields.Float(string='Fixed Discount',compute='_compute_discount', readonly=False, store=True, )
    fld_discount_percent = fields.Float(string='Discount %',help='Discount percentage from total amount')

    # Computed fields
    fld_total = fields.Float(string='Total',  compute='_compute_totals', store=True)
    fld_remain = fields.Float(string='Remain',  compute='_compute_totals', store=True)
    fld_win = fields.Float(string='Winning',  compute='_compute_totals', store=True)

    # Related data
    fld_sells_goods_ids = fields.One2many('mdl_sells_goods', 'fld_sells_id', string="Goods")
    fld_customers_in_ids = fields.One2many('mdl_customers_in', 'fld_sells_id', string="Imports")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('sell_sqnce')
            vals['fld_customers_in_ids'] = [(0, 0, {'fld_date': vals['fld_date'],
                                                  'fld_paying': vals['fld_paying'],
                                                  'fld_is_pay': True,
                                                  'fld_customer_id': vals['fld_customer_id']})]
        return super(cls_sells, self).create(vals_list)

    def write(self, vals):
        customer = vals.get('fld_customer_id')
        xdate = vals.get('fld_date')
        xpaying = vals.get('fld_paying')

        # Only update customers_in if there are actual changes
        if customer or xdate or xpaying:
            xtbl = self.env['mdl_customers_in']
            xdomain = [('fld_sells_id', '=', self.id)]
            xdomain2 = xdomain.copy()
            xdomain2.append(('fld_is_pay', '=', True))

            if customer:
                records = xtbl.search(xdomain)
                if records:
                    records.fld_customer_id = customer

            records = xtbl.search(xdomain2)
            if records:
                update_vals = {}
                if xdate:
                    update_vals['fld_date'] = xdate
                if xpaying:
                    update_vals['fld_paying'] = xpaying

                if update_vals:
                    records.write(update_vals)

        return super(cls_sells, self).write(vals)

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            domain = ['|', '|', ('name', operator, name), ('fld_ref', operator, name),
                      ('fld_customer_id.name', operator, name)]
            return self.search(domain + args, limit=limit).name_get()
        return super(cls_sells, self).name_search(name=name, args=args, operator=operator, limit=limit)

    # ======================= Constraints =======================
    @api.constrains('fld_date')
    def _check_date(self):
        """Validate date is not in future"""
        for record in self:
            if record.fld_date and record.fld_date > fields.Date.today():
                raise UserError(_('Date cannot be in the future'))

    @api.constrains('fld_paying', 'fld_discount', 'fld_discount_percent')
    def _check_amounts(self):
        """Validate payment and discount amounts"""
        for record in self:
            if record.fld_paying and record.fld_paying < 0:
                raise UserError(_('Payment amount cannot be negative'))
            if record.fld_discount and record.fld_discount < 0:
                raise UserError(_('Fixed discount amount cannot be negative'))
            if record.fld_discount_percent and record.fld_discount_percent < 0:
                raise UserError(_('Discount percentage cannot be negative'))
            if record.fld_discount_percent and record.fld_discount_percent > 100:
                raise UserError(_('Discount percentage cannot exceed 100%'))

    @api.constrains('fld_customer_id')
    def _check_customer_restriction(self):
        """Check if customer is allowed for sales"""
        for record in self:
            if record.fld_customer_id and record.fld_customer_id.has_restriction:
                raise UserError(_(
                    'Cannot create sale for restricted customer: %s\n'
                    'Customer Balance: %s\n'
                    'Reason: Customer has sales restriction due to outstanding balance or manual restriction'
                ) % (
                    record.fld_customer_id.name,
                    record.fld_customer_id.balance
                ))

    # ========================= Onchange Functions ==========================
    @api.onchange('fld_customer_id')
    def _onchange_customer(self):
        """Display customer balance and restriction status when customer is selected"""
        if self.fld_customer_id:
            customer = self.fld_customer_id
            if customer.has_restriction:
                return {
                    'warning': {
                        'title': _('Customer Restriction Warning'),
                        'message': _(
                            'Customer: %s\n'
                            'Balance: %s\n'
                            'Status: RESTRICTED - Cannot create sales for this customer due to outstanding balance or manual restriction'
                        ) % (customer.name, customer.balance)
                    }
                }
        return {}

    # ======================= Computed Fields =======================
    @api.depends('fld_total', 'fld_discount_percent')
    def _compute_discount(self):
        for record in self:
            if record.fld_discount_percent > 0:
                record.fld_discount = (record.fld_discount_percent / 100) * record.fld_total

    @api.depends('fld_sells_goods_ids.fld_clc_sell', 'fld_sells_goods_ids.fld_win', 'fld_paying', 'fld_discount')
    def _compute_totals(self):
        """Compute total, remain, and winning amounts with both discount types"""
        for record in self:
            # Calculate total from goods
            total = sum(goods.fld_clc_sell for goods in record.fld_sells_goods_ids)
            record.fld_total = total

            # Calculate total discount (fixed + percentage)
            paying = record.fld_paying or 0
            fixed_discount = record.fld_discount or 0

            record.fld_remain = total - paying - fixed_discount

            # Calculate winning
            win = sum(goods.fld_win for goods in record.fld_sells_goods_ids)
            record.fld_win = win + fixed_discount