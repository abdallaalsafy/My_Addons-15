# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint
from .expense import RealEstateExpense


class RealEstatePaymentInstallment(models.Model):
    _name = 'real.estate.payment.installment'
    _description = 'Real Estate Payment Installment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date'


    name = fields.Char(string='Installment Reference', required=True, copy=False, default=lambda self: _('New'))
    paid_date = fields.Date(string='Paid Date', tracking=True)

    # Relations
    property_id = fields.Many2one('real.estate.property', string='Property', required=True, tracking=True, index=True, ondelete='cascade')
    investment_id = fields.Many2one(related="property_id.investment_id", store=True)
    is_purchased = fields.Boolean(related="property_id.is_purchased", store=True)
    contact_id = fields.Many2one(related="property_id.contact_id", store=True)
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    
    # Payment Details
    amount = fields.Monetary(string='Amount', required=True, tracking=True, currency_field='company_currency')
    due_date = fields.Date(string='Due Date', required=True, tracking=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
    ], string='Status', default='draft', tracking=True)
    payment_method = fields.Selection(RealEstateExpense._SELECTION_PAYMENT_METHOD, string='Payment Method', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    
    notes = fields.Text(string='Notes')

# ========================= Built-In Function =========================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
           
            code = "real.estate.purchase.payment" if vals.get('is_purchased') == True else "real.estate.sale.payment"
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(code)
        
        rtn = super(RealEstatePaymentInstallment, self).create(vals_list)

        rtn.validation_on_create_update_delete()

        return rtn

    def write(self, vals):
        self.validation_on_create_update_delete()
        return super(RealEstatePaymentInstallment, self).write(vals)

    def unlink(self):
        self.validation_on_create_update_delete()
        return super(RealEstatePaymentInstallment, self).unlink()

    # =========================== Action Functions ===========================

    def action_mark_paid(self):
        """Mark installment as paid"""
        self.write({'status': 'paid'})

    def action_mark_draft(self):
        """Mark installment as draft"""
        self.write({'status': 'draft'})

    # ========================= Constrain Functions =================================

    @api.constrains('amount')
    def _check_amount_positive(self):
        for installment in self:
            if installment.amount <= 0:
                raise ValidationError(_('Amount must be positive.'))
            
    @api.constrains('due_date', 'paid_date', 'property_id')
    def _check_due_date_vs_transaction_date(self):
        """Ensure payment due date is not earlier than purchase/sale date"""
        for installment in self:
            if installment.due_date < installment.property_id.property_date or (installment.paid_date and installment.paid_date < installment.property_id.property_date):
                paid_date_msg = (_(', Paid date: %s') % installment.paid_date if installment.paid_date else '')
                if installment.is_purchased:
                    raise ValidationError(_('Payment due date or paid date cannot be earlier than property purchase date. '
                                            'Purchase date: %s, Due date: %s%s') % 
                                        (installment.property_id.property_date, installment.due_date, paid_date_msg))
                elif installment.property_id.status == 'confirmed':
                    raise ValidationError(_('Payment due date or paid date cannot be earlier than sale date. '
                                            'Sale date: %s, Due date: %s%s') % 
                                        (installment.property_id.property_date, installment.due_date, paid_date_msg))

    # =========================== Onchange Functions ===========================
    
    @api.onchange('is_purchased')
    def _onchange_is_purchased(self):
        """Filter property_id domain based on payment_type"""
        if not self.is_purchased:
            # Show only sold properties for sale payments
            return {'domain': {'property_id': [('is_purchased', '=', False)]}}
        else:
            # Show only purchased properties for purchase payments
            return {'domain': {'property_id': [('is_purchased', '=', True)]}}

    # =========================== Logic Functions ===========================

    def validation_on_create_update_delete(self):
        for payment in self:
            if payment.property_id.investment_id.status != 'opening':
                raise ValidationError(_('Cannot update or delete or create payment when investment status is not opening.'))

            if payment.property_id.status == 'draft' and payment.is_purchased == False:
                raise ValidationError(_('Cannot update or delete or create payment when sale property status is draft.'))
