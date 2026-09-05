# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RealEstateInvestmentPayment(models.Model):
    _name = 'real.estate.investment.payment'
    _description = 'Real Estate Investment Payment Installment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc'

    name = fields.Char(string='Payment Reference', required=True, copy=False, default=lambda self: _('New'))
    # Relations
    investment_id = fields.Many2one('real.estate.property.investment', string='Investment', required=True,
                   domain="[('investment_method', '=', 'amount')]", tracking=True, ondelete='cascade')
    partner_id = fields.Many2one('real.estate.partner', string='Partner', related='investment_id.partner_id', store=True, readonly=True)
    # Payment Details
    amount = fields.Float(string='Payment Amount', required=True, tracking=True)
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.today, tracking=True)
    # Notes
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.investment.payment') or _('New')
        return super(RealEstateInvestmentPayment, self).create(vals_list)

    def write(self, vals):
        # Check if investment is confirmed, distributed, or withdrawn
        if self.investment_id and self.investment_id.status != 'confirmed':
            raise ValidationError(_('Cannot edit payment lines for unconfirmed investments.'))
        
        return super(RealEstateInvestmentPayment, self).write(vals)

    def unlink(self):
        # Check if investment is confirmed, distributed, or withdrawn
        for payment in self:
            if payment.investment_id and payment.investment_id.status != 'confirmed':
                raise ValidationError(_('Cannot delete payment lines for unconfirmed investments.'))
        
        return super(RealEstateInvestmentPayment, self).unlink()

    # ============================ Constrains Methods ============================
    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_('Payment amount must be positive.'))

    @api.constrains('payment_date', 'investment_id')
    def _check_payment_date_vs_investment_date(self):
        """Ensure payment date is not earlier than investment date"""
        for payment in self:
            if payment.payment_date and payment.investment_id and payment.investment_id.investment_date:
                if payment.payment_date < payment.investment_id.investment_date:
                    raise ValidationError(_('Payment date cannot be earlier than investment date. '
                                          'Investment date: %s, Payment date: %s') % 
                                        (payment.investment_id.investment_date, payment.payment_date))

    @api.constrains('investment_id')
    def _check_investment_status(self):
        """Ensure investment is confirmed"""
        for payment in self:
            if payment.investment_id and payment.investment_id.status != 'confirmed':
                raise ValidationError(_('Investment must be confirmed to add payment lines.'))

    @api.constrains('investment_id')
    def _check_investment_method(self):
        """Ensure investment method is amount-based (not percentage-based)"""
        for payment in self:
            if payment.investment_id and payment.investment_id.investment_method == 'percentage':
                raise ValidationError(_('Cannot add payment lines for percentage-based investments. '
                                      'Payment lines are only allowed for amount-based investments.'))
