# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RealEstateInvestmentPayment(models.Model):
    _name = 'real.estate.investment.payment'
    _description = 'Real Estate Investment Payment Installment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'investment_id,payment_date'

    name = fields.Char(string='Reference', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    investment_id = fields.Many2one('real.estate.investment', string='Investment', required=True, tracking=True, ondelete='cascade',
                                    domain="[('status', '=', 'opening')]")
    partner_id = fields.Many2one(related='investment_id.partner_id', store=True,)

    amount = fields.Float(string='Amount', required=True, tracking=True)
    payment_date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    notes = fields.Text(string='Notes')

    #========================== Built-In Function ===================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.investment.payment') or _('New')
        rtn = super(RealEstateInvestmentPayment, self).create(vals_list)

        self.get_percentage_value(rtn.mapped('investment_id')) 

        return rtn

    def write(self, vals):
        old_investments = self.mapped('investment_id')

        all_fields_allowed = set(vals).issubset({'notes', 'payment_date'})
        self.mapped('investment_id').validation_update_delete(all_fields_allowed=all_fields_allowed)

        rtn = super(RealEstateInvestmentPayment, self).write(vals)
        
        if 'amount' in vals or 'investment_id' in vals:
            investments = self.mapped('investment_id') | old_investments
            self.get_percentage_value(investments)

        return rtn

    def unlink(self):
        self.mapped('investment_id').validation_update_delete()

        investments = self.mapped('investment_id')
        rtn = super(RealEstateInvestmentPayment, self).unlink()

        self.get_percentage_value(investments) 

        return rtn

    # ============================ Constrains Methods ============================

    @api.constrains('investment_id')
    def _check_deal_id_confirmed_sold_properties(self):
        for payment in self:
            if payment.investment_id.deal_id.confirmed_sold_properties_count > 0:
                raise ValidationError(_('Cannot add payment lines for investments with confirmed sold properties.'))

            if payment.investment_id.deal_id.total_investments_percentage > 100 and payment.investment_id.investment_method == 'percentage':
                raise ValidationError(_('Cannot add payment lines for investments with total investments percentage > 100 and percentage method.'))

    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_('Payment amount must be positive.'))

    @api.constrains('payment_date', 'investment_id')
    def _check_payment_date_vs_investment_date(self):
        """Ensure payment date is not earlier than investment date"""
        for payment in self:
            if payment.payment_date < payment.investment_id.investment_date:
                raise ValidationError(_('Payment date cannot be earlier than investment date. '
                                        'Investment date: %s, Payment date: %s') % 
                                    (payment.investment_id.investment_date, payment.payment_date))

# =================================== Logic Functions ===================================

    def get_percentage_value(self,investments_ids):
        deals = investments_ids.mapped('deal_id')
        for deal in deals:
            if deal.investment_method == 'amount':
                investments = deal.investment_ids
                total_investments = sum(inv.down_payment for inv in investments)
                for investment in investments:
                    if total_investments > 0:
                        investment.percentage = (investment.down_payment / total_investments) * 100
                    else:
                        investment.percentage = 0.0
