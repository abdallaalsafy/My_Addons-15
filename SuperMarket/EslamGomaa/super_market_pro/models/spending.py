from odoo import models, fields, api, _
from odoo.exceptions import UserError

class cls_spending(models.Model):
    _name = 'mdl_spending'
    _description = 'Table Of All Spending'
    _order = "id desc"


    name = fields.Char(string="Code", default=lambda self: _('New'))
    fld_date = fields.Date(string='Date', required=True, )
    fld_paying = fields.Float(string='Paying', )
    fld_notes = fields.Text(string='Notes')
    fld_catg_id = fields.Many2one('mdl_catg_spending', string="Category Spending",required=True,ondelete='restrict')


    # ======================= Built-in Functions =======================
    @api.model_create_multi
    def create(self, vals_list):
        """Create spending records with sequence"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('sp_sqnce')
        return super(cls_spending, self).create(vals_list)

    # ======================= Constraints =======================
    @api.constrains('fld_paying')
    def _check_paying_amount(self):
        """Validate spending amount is greater than zero"""
        for record in self:
            if record.fld_paying <= 0:
                raise UserError(_('Spending amount must be greater than zero!'))

    @api.constrains('fld_date')
    def _check_date(self):
        """Validate date is not in future"""
        for record in self:
            if record.fld_date and record.fld_date > fields.Date.today():
                raise UserError(_('Date cannot be in the future'))
