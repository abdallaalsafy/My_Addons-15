from odoo import models, fields, api, _

class cls_vendors(models.Model):
    _name = 'mdl_vendors'
    _description = 'Table Of All Vendors'
    _order = "name"
    _sql_constraints = [('uniqueVendorsName', 'unique (name,fld_star_name)', 'Vendor Name Already Exists')]

    # Vendor basic data fields
    name = fields.Char(string='Name', required=True, index=True)
    fld_star_name = fields.Char(string='Star Name', index=True)
    fld_phone = fields.Char(string='Phone',size=11)
    fld_address = fields.Char(string='Address')
    active = fields.Boolean(default=True)
    fld_notes = fields.Text(string='Notes')

    # Relations with other tables
    fld_vendors_in_ids=fields.One2many("mdl_vendors_in","fld_vendor_id",readonly=True)
    fld_vendors_out_ids = fields.One2many("mdl_vendors_out", "fld_vendor_id",readonly=True)
    fld_buys_ids = fields.One2many("mdl_buys", "fld_vendor_id",readonly=True)
    fld_buys_r_ids = fields.One2many("mdl_buys_r", "fld_vendor_id",readonly=True)
    
    # Computed fields for smart buttons
    buys_count = fields.Integer(compute='_compute_counts', string='Purchases')
    buys_r_count = fields.Integer(compute='_compute_counts', string='Return Purchases')
    vendors_in_count = fields.Integer(compute='_compute_counts', string='Payments In')
    vendors_out_count = fields.Integer(compute='_compute_counts', string='Payments Out')

    # Computed fields for vendors balance
    total_buys = fields.Float(compute='_compute_balance', string='Total Buys', store=True)
    total_payments = fields.Float(compute='_compute_balance', string='Total Payments', store=True)
    balance = fields.Float(compute='_compute_balance', string='Balance', store=True,
                           help='Positive balance = customer owes money, Negative = customer has credit')

    # ======================= Built-in Functions =======================
    # Enhanced search function for searching by name, star name, or phone
    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            domain = ['|', '|', ('name', operator, name), ('fld_star_name', operator, name),
                      ('fld_phone', operator, name)]
            return self.search(domain + args, limit=limit).name_get()
        return super(cls_vendors, self).name_search(name=name, args=args, operator=operator, limit=limit)

    # ======================= Compute Functions =======================
    def _compute_counts(self):
        for vendor in self:
            vendor.buys_count = len(vendor.fld_buys_ids)
            vendor.buys_r_count = len(vendor.fld_buys_r_ids)
            vendor.vendors_in_count = len(vendor.fld_vendors_in_ids)
            vendor.vendors_out_count = len(vendor.fld_vendors_out_ids)

    def action_view_buys(self):
        action = {
            'name': 'Purchases',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_buys',
            'view_mode': 'tree,form',
            'domain': [('fld_vendor_id', '=', self.id)],
            'context': {'default_fld_vendor_id': self.id}
        }
        return action

    @api.depends('fld_buys_ids', 'fld_buys_r_ids', 'fld_vendors_in_ids', 'fld_vendors_out_ids',
                 'fld_buys_ids.fld_total', 'fld_buys_ids.fld_discount',
                 'fld_buys_r_ids.fld_total', 'fld_buys_r_ids.fld_discount',
                 'fld_vendors_in_ids.fld_paying', 'fld_vendors_out_ids.fld_paying', )
    def _compute_balance(self):
        for vendor in self:
            # Calculate total sales amount
            total_buys = sum((buy.fld_total - buy.fld_discount) for buy in vendor.fld_buys_ids)
            total_return_buys = sum((buy.fld_total - buy.fld_discount) for buy in vendor.fld_buys_r_ids)

            # Calculate total payments
            total_payments_in = sum(payment.fld_paying for payment in vendor.fld_vendors_in_ids)
            total_payments_out = sum(payment.fld_paying for payment in vendor.fld_vendors_out_ids)

            # Calculate totals
            vendor.total_buys = total_buys - total_return_buys
            vendor.total_payments =  total_payments_in - total_payments_out
            vendor.balance = vendor.total_buys + vendor.total_payments

    # ======================= Action Functions =======================
    def action_view_buys_r(self):
        action = {
            'name': 'Return Purchases',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_buys_r',
            'view_mode': 'tree,form',
            'domain': [('fld_vendor_id', '=', self.id)],
            'context': {'default_fld_vendor_id': self.id}
        }
        return action

    def action_view_vendors_in(self):
        action = {
            'name': 'Payments In',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_vendors_in',
            'view_mode': 'tree,form',
            'domain': [('fld_vendor_id', '=', self.id)],
            'context': {'default_fld_vendor_id': self.id}
        }
        return action

    def action_view_vendors_out(self):
        action = {
            'name': 'Payments Out',
            'type': 'ir.actions.act_window',
            'res_model': 'mdl_vendors_out',
            'view_mode': 'tree,form',
            'domain': [('fld_vendor_id', '=', self.id)],
            'context': {'default_fld_vendor_id': self.id}
        }
        return action