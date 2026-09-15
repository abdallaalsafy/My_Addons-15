# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RealEstatePartnershipPayment(models.Model):
    _name = 'real.estate.partnership.payment'
    _description = 'Real Estate Partnership Payment Installment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partnership_id,payment_date'


    name = fields.Char(string='Reference', required=True, readonly=True, copy=False, default=lambda self: _('New'))
    partnership_id = fields.Many2one('real.estate.partnership', string='Partnership', required=True, tracking=True, ondelete='cascade',
                                    domain="[('status', '=', 'opening')]")
    partner_id = fields.Many2one(related='partnership_id.partner_id', store=True,)
    investment_id = fields.Many2one(related='partnership_id.investment_id', store=True,)
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    
    amount = fields.Monetary(string='Amount', required=True, tracking=True, currency_field='company_currency')
    payment_date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    notes = fields.Text(string='Notes')

    auto_create_transaction = fields.Boolean(string='Auto-create Transaction',default=lambda self: self.env.company.auto_create_transaction_default,tracking=True,
                            help='If checked, saving this payment will automatically create a matching deposit transaction '
                                    'for the partner, so you do not need to create it manually beforehand. '
                                    'This option cannot be changed anymore once the payment has been saved.')

    #========================== Built-In Function ===================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.partnership.payment') or _('New')
        rtn = super(RealEstatePartnershipPayment, self).create(vals_list)

        # If auto_create_transaction is checked, create a matching deposit transaction for the partner
        for payment in rtn:
            if payment.auto_create_transaction:
                self.env['real.estate.transaction'].create({
                    'partner_id': payment.partner_id.id,
                    'transaction_type': 'deposit',
                    'amount': payment.amount,
                    'transaction_date': payment.payment_date,
                    'description': _('Auto-created from partnership payment %s (%s).') % (payment.name, payment.partnership_id.name),
                })

        self.get_percentage_value(rtn.mapped('partnership_id')) 

        return rtn

    def write(self, vals):
        # If auto_create_transaction is being changed, prevent it from being changed after the payment has been saved
        if 'auto_create_transaction' in vals:
            for payment in self:
                if payment.auto_create_transaction != vals['auto_create_transaction']:
                    raise ValidationError(_('The "Auto-create Transaction" option cannot be changed after the payment has been saved.'))
                
        old_partnerships = self.mapped('partnership_id')

        all_fields_allowed = set(vals).issubset({'notes', 'payment_date'})
        self.mapped('partnership_id').validation_update_delete(all_fields_allowed=all_fields_allowed)

        rtn = super(RealEstatePartnershipPayment, self).write(vals)
        
        if 'amount' in vals or 'partnership_id' in vals:
            partnerships = self.mapped('partnership_id') | old_partnerships
            self.get_percentage_value(partnerships)

        return rtn

    def unlink(self):
        self.mapped('partnership_id').validation_update_delete()

        partnerships = self.mapped('partnership_id')
        rtn = super(RealEstatePartnershipPayment, self).unlink()

        self.get_percentage_value(partnerships) 

        return rtn

    # ============================ Constrains Methods ============================

    @api.constrains('partnership_id')
    def _check_investment_id_confirmed_sold_properties(self):
        for payment in self:
            if payment.partnership_id.investment_id.confirmed_sold_properties_count > 0:
                raise ValidationError(_('Cannot add payment lines for partnerships with confirmed sold properties.'))

            if payment.partnership_id.investment_id.total_partnerships_percentage > 100 and payment.partnership_id.investment_id.investment_method == 'percentage':
                raise ValidationError(_('Cannot add payment lines for partnerships with total partnerships percentage > 100 and percentage method.'))

    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_('Payment amount must be positive.'))

    @api.constrains('payment_date', 'partnership_id')
    def _check_payment_date_vs_partnership_date(self):
        """Ensure payment date is not earlier than partnership date"""
        for payment in self:
            if payment.payment_date < payment.partnership_id.partnership_date:
                raise ValidationError(_('Payment date cannot be earlier than partnership date. '
                                        'partnership date: %s, Payment date: %s') % 
                                    (payment.partnership_id.partnership_date, payment.payment_date))

# =================================== Logic Functions ===================================

    def get_percentage_value(self,partnerships_ids):
        investments = partnerships_ids.mapped('investment_id')
        for investment in investments:
            if investment.investment_method == 'amount':
                partnerships = investment.partnership_ids
                total_partnerships = sum(inv.down_payment for inv in partnerships)
                for partnership in partnerships:
                    if total_partnerships > 0:
                        partnership.percentage = (partnership.down_payment / total_partnerships) * 100
                    else:
                        partnership.percentage = 0.0
