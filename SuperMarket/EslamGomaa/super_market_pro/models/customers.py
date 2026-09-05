from odoo import models, fields, api, _

class cls_customers(models.Model):
    _name = 'mdl_customers'
    _description = 'Table Of All Customers'
    _order = "name"
    _sql_constraints = [('uniqueCustomersName', 'unique (name,fld_star_name)', 'Customer Name Already Exists')]


    # Customer basic data fields
    name = fields.Char(string='Name', required=True, index=True)
    fld_star_name = fields.Char(string='Star Name', index=True)
    fld_phone = fields.Char(string='Phone',size=11)
    fld_address = fields.Char(string='Address')
    fld_notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    # Relations with other tables
    fld_customers_in_ids=fields.One2many("mdl_customers_in","fld_customer_id",readonly=True)
    fld_customers_out_ids = fields.One2many("mdl_customers_out", "fld_customer_id",readonly=True)
    fld_sells_ids = fields.One2many("mdl_sells", "fld_customer_id",readonly=True)
    fld_sells_r_ids = fields.One2many("mdl_sells_r", "fld_customer_id",readonly=True)
    
    # Computed fields for smart buttons
    sells_count = fields.Integer(compute='_compute_counts', string='Sales')
    sells_r_count = fields.Integer(compute='_compute_counts', string='Return Sales')
    customers_in_count = fields.Integer(compute='_compute_counts', string='Payments In')
    customers_out_count = fields.Integer(compute='_compute_counts', string='Payments Out')

    # Computed fields for customer balance and restrictions
    total_sales = fields.Float(compute='_compute_balance', string='Total Sales', store=True)
    total_payments = fields.Float(compute='_compute_balance', string='Total Payments', store=True)
    balance = fields.Float(compute='_compute_balance', string='Balance', store=True,
                           help='Positive balance = customer owes money, Negative = customer has credit')
    has_restriction = fields.Boolean(compute='_compute_restriction', string='Has Sales Restriction', store=True, readonly=False)
    restriction_amount = fields.Float(string='Restriction Amount', help='Maximum allowed balance before restriction')

    # ======================= Built-in Functions =======================
    # Enhanced search function for searching by name, star name, or phone
    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            domain = ['|', '|', ('name', operator, name), ('fld_star_name', operator, name),
                      ('fld_phone', operator, name)]
            return self.search(domain + args, limit=limit).name_get()
        return super(cls_customers, self).name_search(name=name, args=args, operator=operator, limit=limit)

    # ======================= Compute Functions =======================
    def _compute_counts(self):
        for customer in self:
            customer.sells_count = len(customer.fld_sells_ids)
            customer.sells_r_count = len(customer.fld_sells_r_ids)
            customer.customers_in_count = len(customer.fld_customers_in_ids)
            customer.customers_out_count = len(customer.fld_customers_out_ids)

    @api.depends('fld_sells_ids', 'fld_sells_r_ids', 'fld_customers_in_ids', 'fld_customers_out_ids',
                 'fld_sells_ids.fld_total', 'fld_sells_ids.fld_discount',
                 'fld_sells_r_ids.fld_total', 'fld_sells_r_ids.fld_discount',
                 'fld_customers_in_ids.fld_paying', 'fld_customers_out_ids.fld_paying',)
    def _compute_balance(self):
        for customer in self:
            # Calculate total sales amount
            total_sales = sum((sell.fld_total-sell.fld_discount) for sell in customer.fld_sells_ids)
            total_return_sales = sum((sell.fld_total-sell.fld_discount) for sell in customer.fld_sells_r_ids)

            # Calculate total payments
            total_payments_in = sum(payment.fld_paying for payment in customer.fld_customers_in_ids)
            total_payments_out = sum(payment.fld_paying for payment in customer.fld_customers_out_ids)

            # Calculate totals
            customer.total_sales = total_sales - total_return_sales
            customer.total_payments = total_payments_out - total_payments_in
            customer.balance = customer.total_sales + customer.total_payments

    @api.depends('restriction_amount', 'balance')
    def _compute_restriction(self):
        for customer in self:
            if customer.restriction_amount > 0:
                customer.has_restriction = customer.restriction_amount >= customer.balance

    # ======================= Action Functions =======================
    def action_view_sells(self):
        action = {
            'name': 'Sales',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_sells',
            'view_mode': 'tree,form',
            'domain': [('fld_customer_id', '=', self.id)],
            'context': {'default_fld_customer_id': self.id}
        }
        return action

    def action_view_sells_r(self):
        action = {
            'name': 'Return Sales',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_sells_r',
            'view_mode': 'tree,form',
            'domain': [('fld_customer_id', '=', self.id)],
            'context': {'default_fld_customer_id': self.id}
        }
        return action

    def action_view_customers_in(self):
        action = {
            'name': 'Payments In',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_customers_in',
            'view_mode': 'tree,form',
            'domain': [('fld_customer_id', '=', self.id)],
            'context': {'default_fld_customer_id': self.id}
        }
        return action

    def action_view_customers_out(self):
        action = {
            'name': 'Payments Out',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_customers_out',
            'view_mode': 'tree,form',
            'domain': [('fld_customer_id', '=', self.id)],
            'context': {'default_fld_customer_id': self.id}
        }
        return action