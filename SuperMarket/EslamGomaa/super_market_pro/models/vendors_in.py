from odoo import models, fields, api, _
from odoo.exceptions import UserError

class cls_vendors_in(models.Model):
    _name = 'mdl_vendors_in'
    _description = 'Table Of All Vendor Refund Payments'
    _order = "id desc"

    name = fields.Char(string="Code", default=lambda self: _('New'))
    fld_date = fields.Date(string='Date', required=True, )
    fld_paying = fields.Float(string='Refund Amount', )
    fld_is_pay = fields.Boolean(string="Is Refunded", default=False)
    fld_notes = fields.Text(string='Notes')
    fld_buys_r_id = fields.Many2one('mdl_buys_r', string="Return Purchase Order", ondelete='cascade')
    fld_vendor_id = fields.Many2one('mdl_vendors', string="Vendor", ondelete='restrict')

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
    @api.onchange('fld_buys_r_id')
    def fnc_chng_buys_r_id(self):
        """Set vendor when return purchase order changes"""
        buys_r_id = self.fld_buys_r_id
        if buys_r_id:
            self.fld_vendor_id = buys_r_id.fld_vendor_id

    # ======================= Built-in Functions =======================
    @api.model_create_multi
    def create(self, vals_list):
        """Create vendor refund payment records with sequence"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('in_sqnce')
        return super(cls_vendors_in, self).create(vals_list)

    def unlink(self):
        """Prevent deletion of paid records"""
        for obj in self:
            if obj.fld_is_pay:
                raise UserError(_('You cannot delete this paid record: %s') % obj.name)
        return super(cls_vendors_in, self).unlink()

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.fld_vendor_id:
                name = f"{record.name} - {record.fld_vendor_id.name}"
            result.append((record.id, name))
        return result
