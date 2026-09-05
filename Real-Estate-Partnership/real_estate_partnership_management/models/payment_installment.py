# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint


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
    property_id = fields.Many2one('real.estate.property', string='Property', required=True, tracking=True, index=True, ondelete='cascade')
    contact_id = fields.Many2one('real.estate.contact', string='Contact', required=True, tracking=True, index=True, ondelete='restrict')
    sale_id = fields.Many2one('real.estate.property.sale', string='Sale', index=True, ondelete='cascade')

    # Payment Type
    payment_type = fields.Selection([
        ('purchase', 'Purchase Payment (To Seller)'),
        ('sale', 'Sale Payment (From Buyer)'),
    ], string='Payment Type', required=True, tracking=True, index=True)
    
    # Payment Details
    amount = fields.Float(string='Installment Amount', required=True, tracking=True)
    due_date = fields.Date(string='Due Date', required=True, tracking=True)
    is_down_payment = fields.Boolean(string='Is Down Payment', tracking=True, 
                                    help='Check if this payment is a down payment for the property')
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
    ], string='Status', default='draft', tracking=True)
    
    # Payment Method
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
    ], string='Payment Method', tracking=True)
    
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    
    # Notes
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                if vals.get('payment_type') == 'purchase':
                    vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.purchase.payment') or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.sale.payment') or _('New')
        
        return super(RealEstatePaymentInstallment, self).create(vals_list)

    def write(self, vals):
        installment_affecting_fields = ['amount', 'property_id','status']
        if any(field in vals for field in installment_affecting_fields):
            for installment in self:
                # Prevent updating down payment installments if down_payment field is set
                if installment.is_down_payment and not self.env.context.get('update_from_sale_code', False):
                    raise ValidationError(_('Cannot update down payment installment while down payment is set on the property.'))
        return super(RealEstatePaymentInstallment, self).write(vals)

    def unlink(self):
        # Check if property is sold (for purchase payments)
        for installment in self:
            # Prevent deleting down payment installments if down_payment field is set
            if installment.is_down_payment:
                if installment.payment_type == 'purchase' and installment.property_id.down_payment > 0:
                    raise ValidationError(_('Cannot delete down payment installment while down payment is set on the property.'))
                elif installment.payment_type == 'sale' and installment.property_id.sale_id.down_payment > 0:
                    raise ValidationError(_('Cannot delete down payment installment while down payment is set on the sale.'))
        
        return super(RealEstatePaymentInstallment, self).unlink()

    # =========================== Action Functions ===========================

    def action_mark_paid(self):
        """Mark installment as paid"""
        self.write({'status': 'paid'})

    def action_mark_draft(self):
        """Mark installment as draft"""
        self.write({'status': 'draft'})

    # =========================== Validation Functions ===========================
    
    @staticmethod
    def validate_property_for_purchase_payment(property):
        """
        Validate if property can accept new purchase payment
        Raises ValidationError if property cannot accept purchase payment
        """
        if property.is_child:
            raise ValidationError(_('Cannot create purchase payments for child properties.'))
    
    @staticmethod
    def validate_property_for_sale_payment(property):
        """
        Validate if property can accept new sale payment
        Raises ValidationError if property cannot accept sale payment
        """
        if property.status != 'sold':
            raise ValidationError(_('Cannot create sale payments for properties that are not sold yet.'))

    # ========================= Constrain Functions =================================

    @api.constrains('amount')
    def _check_amount_positive(self):
        for installment in self:
            if installment.amount <= 0:
                raise ValidationError(_('Amount must be positive.'))

    @api.constrains('payment_type', 'property_id')
    def _check_payment_type_and_property(self):
        for installment in self:
            # Cannot create sale payment for property that is not sold (skip for down payments)
            if installment.payment_type == 'sale' and not installment.is_down_payment:
                self.validate_property_for_sale_payment(installment.property_id)
            
            # Cannot create purchase payment for child properties
            if installment.payment_type == 'purchase':
                self.validate_property_for_purchase_payment(installment.property_id)

    @api.constrains('payment_type', 'contact_id', 'property_id')
    def _check_contact_matches_property(self):
        for installment in self:
            if installment.payment_type == 'purchase':
                # For purchase payments, contact must match property seller
                if installment.property_id.seller_id and installment.contact_id != installment.property_id.seller_id:
                    raise ValidationError(_('For purchase payments, the contact must match the property seller.'))
            elif installment.payment_type == 'sale':
                # For sale payments, contact must match property buyer
                if installment.property_id.sold_to_contact_id and installment.contact_id != installment.property_id.sold_to_contact_id:
                    raise ValidationError(_('For sale payments, the contact must match the property buyer.'))

    @api.constrains('due_date', 'payment_type', 'property_id', 'sale_id')
    def _check_due_date_vs_transaction_date(self):
        """Ensure payment due date is not earlier than purchase/sale date"""
        for installment in self:
            if installment.payment_type == 'purchase' and installment.due_date and installment.property_id and installment.property_id.purchase_date:
                if installment.due_date < installment.property_id.purchase_date:
                    raise ValidationError(_('Payment due date cannot be earlier than property purchase date. '
                                          'Purchase date: %s, Due date: %s') % 
                                        (installment.property_id.purchase_date, installment.due_date))
            elif installment.payment_type == 'sale' and installment.due_date and installment.sale_id and installment.sale_id.sale_date:
                if installment.due_date < installment.sale_id.sale_date:
                    raise ValidationError(_('Payment due date cannot be earlier than sale date. '
                                          'Sale date: %s, Due date: %s') % 
                                        (installment.sale_id.sale_date, installment.due_date))

    # =========================== Onchange Functions ===========================
    
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        """Filter property_id domain based on payment_type"""
        if self.payment_type == 'sale':
            # Show only sold properties for sale payments
            return {'domain': {'property_id': [('status', '=', 'sold'),('has_any_children', '=', False)]}}
        elif self.payment_type == 'purchase':
            # Show only child properties for purchase payments
            return {'domain': {'property_id': [('is_child', '=', False)]}}
        else:
            return {'domain': {'property_id': []}}

    @api.onchange('payment_type', 'property_id')
    def _onchange_payment_type(self):
        """Filter property_id domain based on payment_type"""
        if self.payment_type == 'sale':
            self.sale_id = self.property_id.sale_id
            self.contact_id = self.property_id.sold_to_contact_id
        else:
            self.sale_id = False
            self.contact_id = self.property_id.seller_id

    # =========================== Compute Functions ===========================
