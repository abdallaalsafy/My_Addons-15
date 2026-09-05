# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PurchasePaymentReceiptsWizard(models.TransientModel):
    _name = 'purchase.payment.receipts.wizard'
    _description = 'Purchase Payment Receipts Generator Wizard'

    property_id = fields.Many2one('real.estate.property', string='Property', required=True, readonly=True)
    sale_id = fields.Many2one('real.estate.property.sale', string='Sale', readonly=True)
    
    # Payment type
    payment_type = fields.Selection([
        ('purchase', 'Purchase Payment (To Seller)'),
        ('sale', 'Sale Payment (From Buyer)'),
    ], string='Payment Type', required=True, default='purchase', readonly=True)
    
    # Amount field - default to remaining purchase/sale amount
    amount = fields.Float(string='Amount', help='Total amount to be distributed across receipts', compute='_compute_amount')
    
    # Date or installment field
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today,
                             help='First installment due date')
    
    # Duration field
    duration = fields.Integer(string='Duration', required=True, default=1,
                              help='Duration in the selected unit')
    
    # Duration unit (optional: month, year, day)
    duration_unit = fields.Selection([
        ('month', 'Month'),
        ('year', 'Year'),
        ('day', 'Day'),
    ], string='Duration Unit', required=True, default='month')
    
    # Number of receipts
    number_of_receipts = fields.Integer(string='Number of Receipts', required=True, default=1,
                                        help='How many payment receipts to create')

    # Receipt generation mode
    generation_mode = fields.Selection([
        ('unpaid', 'Unpaid Only'),
        ('all', 'All (Except Down Payment)'),
    ], string='Generation Mode', required=True, default='unpaid',
       help='Generate receipts for unpaid only or all receipts (except down payment)')
    
    @api.model
    def default_get(self, fields_list):
        res = super(PurchasePaymentReceiptsWizard, self).default_get(fields_list)

        # Handle property context (purchase payments)
        if self._context.get('active_id') and self._context.get('active_model') == 'real.estate.property':
            property_id = self.env['real.estate.property'].browse(self._context['active_id'])
            res['property_id'] = property_id.id
            res['payment_type'] = 'purchase'

        # Handle sale context (sale payments)
        elif self._context.get('active_id') and self._context.get('active_model') == 'real.estate.property.sale':
            sale_id = self.env['real.estate.property.sale'].browse(self._context['active_id'])
            res['sale_id'] = sale_id.id
            res['property_id'] = sale_id.property_id.id
            res['payment_type'] = 'sale'

        return res

    @api.depends('generation_mode')
    def _compute_amount(self):
        """Update amount based on generation mode"""
        for record in self:
            if record.payment_type == 'purchase' and record.property_id:
                if record.generation_mode == 'unpaid':
                    # Calculate unpaid amount
                    record.amount = record.property_id.remaining_purchase_amount
                else:  # all
                    # Calculate total amount (excluding down payment)
                    record.amount = record.property_id.purchase_price - record.property_id.down_payment

            elif record.payment_type == 'sale' and record.sale_id:
                if record.generation_mode == 'unpaid':
                    # Calculate unpaid amount
                    record.amount = record.sale_id.remaining_balance
                else:  # all
                    # Calculate total amount (excluding down payment)
                    record.amount = record.sale_id.sale_price - record.sale_id.down_payment

    def action_generate_receipts(self):
        """Generate purchase or sale payment receipts based on wizard settings"""
        self.ensure_one()

        # Validate
        if self.number_of_receipts <= 0:
            raise ValidationError(_('Number of receipts must be positive.'))
        if self.duration <= 0:
            raise ValidationError(_('Duration must be positive.'))
        if self.amount <= 0:
            raise ValidationError(_('Amount must be positive.'))
        
        # Calculate amount per receipt
        amount_per_receipt = self.amount / self.number_of_receipts
        
        # Validate based on payment type
        if self.payment_type == 'purchase':
            if self.property_id.is_child:
                raise ValidationError(_('Cannot create purchase payments for child properties.'))
            if not self.property_id.seller_id:
                raise ValidationError(_('Property must have a seller to create purchase payments.'))
            contact_id = self.property_id.seller_id.id
        elif self.payment_type == 'sale':
            if not self.sale_id:
                raise ValidationError(_('Sale record is required for sale payments.'))
            if not self.sale_id.buyer_contact_id:
                raise ValidationError(_('Sale must have a buyer contact to create sale payments.'))
            contact_id = self.sale_id.buyer_contact_id.id
        
        # Create receipts
        receipt_vals_list = []
        current_date = self.start_date
        
        for i in range(self.number_of_receipts):
            receipt_vals = {
                'name': _('New'),
                'property_id': self.property_id.id,
                'contact_id': contact_id,
                'payment_type': self.payment_type,
                'amount': amount_per_receipt,
                'due_date': current_date,
                'status': 'draft',
            }
            if self.payment_type == 'sale':
                receipt_vals['sale_id'] = self.sale_id.id
            receipt_vals_list.append(receipt_vals)
            
            # Calculate next date based on duration unit
            if self.duration_unit == 'day':
                current_date = current_date + timedelta(days=self.duration)
            elif self.duration_unit == 'month':
                current_date = current_date + relativedelta(months=self.duration)
            elif self.duration_unit == 'year':
                current_date = current_date + relativedelta(years=self.duration)

        # Delete existing receipts based on generation mode
        domain = [('property_id', '=', self.property_id.id), ('is_down_payment', '=', False), ('payment_type', '=', self.payment_type)]
        if self.generation_mode == 'unpaid':
            domain.append(('status', '=', 'draft'))
        self.env['real.estate.payment.installment'].search(domain).unlink()

        # Create all receipts
        receipts = self.env['real.estate.payment.installment'].create(receipt_vals_list)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment Receipts'),
            'res_model': 'real.estate.payment.installment',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.property_id.id),('payment_type','=',self.payment_type)],
            'context': {'default_property_id': self.property_id.id, 'default_payment_type': self.payment_type},
        }
