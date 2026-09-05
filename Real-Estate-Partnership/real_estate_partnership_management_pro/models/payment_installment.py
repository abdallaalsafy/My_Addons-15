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

    def _get_default_color(self):
    # Generate a random color value between 1 and 11
    # This method is likely used to provide a default color when none is specified
        return randint(1, 11)

    name = fields.Char(string='Installment Reference', required=True, copy=False, default=lambda self: _('New'))
    color = fields.Integer(string='Color', default=_get_default_color)
    
    # Relations
    contract_id = fields.Many2one('real.estate.property', string='Contract', required=True, tracking=True, index=True, ondelete='cascade')
    is_purchased = fields.Boolean(related="contract_id.is_purchased", store=True)
    contact_id = fields.Many2one(related="contract_id.contact_id", store=True)
    
    # Payment Details
    amount = fields.Float(string='Amount', required=True, tracking=True)
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
           
            code = "real.estate.purchase.payment" if vals.get('is_purchase') == True else "real.estate.sale.payment"
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

    @api.constrains('due_date', 'contract_id')
    def _check_due_date_vs_transaction_date(self):
        """Ensure payment due date is not earlier than purchase/sale date"""
        for installment in self:
            if installment.due_date < installment.contract_id.contract_date:
                if installment.is_purchased:
                    raise ValidationError(_('Payment due date cannot be earlier than contract purchase date. '
                                            'Purchase date: %s, Due date: %s') % 
                                        (installment.contract_id.contract_date, installment.due_date))
                elif installment.contract_id.status == 'confirmed':
                    raise ValidationError(_('Payment due date cannot be earlier than sale date. '
                                            'Sale date: %s, Due date: %s') % 
                                        (installment.contract_id.contract_date, installment.due_date))

    # =========================== Onchange Functions ===========================
    
    @api.onchange('is_purchased')
    def _onchange_is_purchased(self):
        """Filter property_id domain based on payment_type"""
        if not self.is_purchased:
            # Show only sold properties for sale payments
            return {'domain': {'contract_id': [('is_purchased', '=', False)]}}
        else:
            # Show only child properties for purchase payments
            return {'domain': {'contract_id': [('is_purchased', '=', True)]}}

    # =========================== Logic Functions ===========================

    def validation_on_create_update_delete(self):
        for payment in self:
            if payment.contract_id.deal_id.status != 'opening':
                raise ValidationError(_('Cannot update or delete or create payment when deal status is not opening.'))

            if payment.contract_id.status == 'draft' and payment.is_purchased == False:
                raise ValidationError(_('Cannot update or delete or create payment when sale contract status is draft.'))
