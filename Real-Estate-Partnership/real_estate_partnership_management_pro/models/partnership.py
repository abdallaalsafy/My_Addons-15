# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

 
class RealEstatePartnership(models.Model):
    _name = 'real.estate.partnership'
    _description = 'Real Estate Partnership'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'investment_id,partnership_date'


    name = fields.Char(string='partnership Reference', required=True, copy=False, default=lambda self: _('New'))
    partnership_date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True, index=True,
                                 domain="[('status', '=', 'active')]",ondelete='restrict')
    investment_id = fields.Many2one('real.estate.investment', string='investment', required=True, tracking=True, index=True,ondelete='cascade',
                              domain="[('status', '=', 'opening'),'|','&',('total_partnerships_percentage', '<', 100),('investment_method', '=', 'percentage'),('investment_method', '=', 'amount')]")
    
    # Related fields for easy access
    investment_method = fields.Selection(related='investment_id.investment_method', store=True)
    status = fields.Selection(related='investment_id.status', store=True, index=True)
    total_cost = fields.Float(related='investment_id.total_investment_cost', store=True)

    # partnership Details
    amount = fields.Float(string='Total Amount', compute='_compute_amount', store=True,)
    down_payment = fields.Float(string='Down Payment', compute='_compute_down_payment', store=True, tracking=True, help='Down payment amount for the partnership')
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_remaining_amount', store=True)
    percentage = fields.Float(string='Percentage %', readonly=True)

    notes = fields.Text(string='Notes')
    # partnership Payment Lines
    payment_line_ids = fields.One2many('real.estate.partnership.payment', 'partnership_id', string='Payment Installments')

    #=========================== Built-in Functions ===========================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.partnership') or _('New')
        
        rtn =  super(RealEstatePartnership, self).create(vals_list)
        return rtn

    def write(self, vals):
        # vals is only allowed to update notes
        all_fields_allowed = set(vals).issubset({'notes'})
        self.validation_update_delete(all_fields_allowed=all_fields_allowed)

        rtn = super(RealEstatePartnership, self).write(vals)

        return rtn

    def unlink(self):
        self.validation_update_delete()

        ren =  super(RealEstatePartnership, self).unlink()
        return ren

    def name_get(self):
        result = []
        for partnership in self:
            name = f"{partnership.name} ({partnership.partner_id.name})"
            result.append((partnership.id, name))
        return result

    # =========================== Compute Functions ===========================

    @api.depends('percentage', 'investment_id.total_investment_cost')
    def _compute_amount(self):
        for partnership in self:
            # Calculate amount from percentage of total cost
            investment_coast = partnership.investment_id.total_investment_cost
            partnership.amount = (partnership.percentage / 100) * investment_coast

    @api.depends('payment_line_ids.amount')
    def _compute_down_payment(self):
        for partnership in self:
            partnership.down_payment = sum(line.amount for line in partnership.payment_line_ids)

    @api.depends('down_payment','amount')
    def _compute_remaining_amount(self):
        for partnership in self:
            partnership.remaining_amount = partnership.amount - partnership.down_payment

    # =========================== Constraints Functions ===========================

    @api.constrains('investment_id')
    def _check_investment_id_confirmed_sold_properties(self):
        for partnership in self:
            if partnership.investment_id.confirmed_sold_properties_count > 0:
                raise ValidationError(_('This investment has confirmed sold properties. Cannot add partnership to this investment.'))

    @api.constrains('partner_id', 'investment_id')
    def _check_unique_partnership(self):
        for partnership in self:
            existing = self.search([
                ('partner_id', '=', partnership.partner_id.id),
                ('investment_id', '=', partnership.investment_id.id),
                ('id', '!=', partnership.id),
            ])
            if existing:
                raise ValidationError(_('Partner already has an partnership to this investment.'))

    @api.constrains('partnership_date', 'investment_id', 'partner_id')
    def _check_partnership_date(self):
        """Ensure partnership date is not earlier than property purchase date"""
        for partnership in self:
            if partnership.partnership_date > fields.Date.today():
                raise ValidationError(_('Partnership date cannot be in the future.'))
            
            if partnership.partnership_date < partnership.investment_id.open_date:
                raise ValidationError(_('Partnership date cannot be earlier than investment open date. '
                                        'investment open date: %s, Partnership date: %s') % 
                                    (partnership.investment_id.open_date, partnership.partnership_date))

            if partnership.partnership_date < partnership.partner_id.join_date:
                raise ValidationError(_('Partnership date cannot be earlier than partner join date. '
                                        'Join date: %s, Partnership date: %s') % 
                                    (partnership.partner_id.join_date, partnership.partnership_date))

# =================================== Logic Functions ===================================

    def validation_update_delete(self,all_fields_allowed=False):
        for partnership in self:
            if partnership.status != 'opening':
                raise ValidationError(_('Partnership is not opening. Cannot update or delete partnership.'))
                    
            if partnership.investment_id.confirmed_sold_properties_count > 0 and not all_fields_allowed:
                raise ValidationError(_('This investment has confirmed sold properties. Cannot update or delete partnership to this investment.'))
