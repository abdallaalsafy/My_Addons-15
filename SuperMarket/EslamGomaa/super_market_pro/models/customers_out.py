from odoo import models, fields, api, _
from odoo.exceptions import UserError

class cls_customers_out(models.Model):
    _name = 'mdl_customers_out'
    _description = 'Table Of All Customer Refund Payments'
    _order = "id desc"

    name = fields.Char(string="Code", default=lambda self: _('New'))
    fld_date = fields.Date(string='Date', required=True, )
    fld_paying = fields.Float(string='Refund Amount', )
    fld_is_pay = fields.Boolean(string="Is Refunded", default=False)
    fld_notes = fields.Text(string='Notes')
    fld_sells_r_id = fields.Many2one('mdl_sells_r', string="Return Sales Order", ondelete='cascade')
    fld_customer_id = fields.Many2one('mdl_customers', string="Customer", ondelete='restrict')

    # ======================= Constraints =======================
    @api.constrains('fld_paying')
    def fnc_check_paying(self):
        """Validate payment amount"""
        for rcrd in self:
            if rcrd.fld_paying <= 0 and not rcrd.fld_is_pay:
                raise UserError(_('Payment amount must be above zero!'))

    @api.constrains('fld_date')
    def _check_date(self):
        """Validate date is not in future"""
        for record in self:
            if record.fld_date and record.fld_date > fields.Date.today():
                raise UserError(_('Date cannot be in the future'))

    # ======================= Onchange Functions =======================
    @api.onchange('fld_sells_r_id')
    def fnc_chng_sells_r_id(self):
        """Set customer when return sales order changes"""
        sells_r_id = self.fld_sells_r_id
        if sells_r_id:
            self.fld_customer_id = sells_r_id.fld_customer_id

    # ======================= Built-in Functions =======================
    @api.model_create_multi
    def create(self, vals_list):
        """Create customer refund payment records with sequence"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('out_sqnce')
        return super(cls_customers_out, self).create(vals_list)

    def unlink(self):
        """Prevent deletion of paid records"""
        for obj in self:
            if obj.fld_is_pay:
                raise UserError(_('You cannot delete this paid record: %s') % obj.name)
        return super(cls_customers_out, self).unlink()

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.fld_customer_id:
                name = f"{record.name} - {record.fld_customer_id.name}"
            result.append((record.id, name))
        return result
