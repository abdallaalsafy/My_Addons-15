# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PropertyPaymentReceiptsWizard(models.TransientModel):
    _name = 'property.payment.receipts.wizard'
    _description = 'Property Payment Receipts Generator Wizard'

    property_id = fields.Many2one('real.estate.property', string='Property', required=True, readonly=True)
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    is_purchased = fields.Boolean(related="property_id.is_purchased", store=True)
    amount = fields.Monetary(string='Amount', currency_field='company_currency', help='Total amount to be distributed across receipts', compute='_compute_amount')
    
    # Date or installment field
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today,
                             help='First installment due date')
    duration = fields.Integer(string='Duration', required=True, default=1,
                              help='Duration in the selected unit')
    # Duration unit (optional: month, year, day)
    duration_unit = fields.Selection([
        ('month', 'Month'),
        ('year', 'Year'),
        ('day', 'Day'),
    ], string='Duration Unit', required=True, default='month')
    number_of_receipts = fields.Integer(string='Number of Receipts', required=True, default=1,
                                        help='How many payment receipts to create')

    # Receipt generation mode
    generation_mode = fields.Selection([
        ('unpaid', 'Unpaid Only'),
        ('all', 'All Installments'),
    ], string='Generation Mode', required=True, default='unpaid',
       help='Generate receipts for unpaid only or all receipts')

# =========================== Compute Functions ===========================

    @api.depends('generation_mode')
    def _compute_amount(self):
        """Update amount based on generation mode"""
        for record in self:
            if record.generation_mode == 'unpaid':
                record.amount = record.property_id.remaining_amount
            else:  # all
                record.amount = record.property_id.property_price - record.property_id.down_payment

# =========================== Action Generate ===========================

    def action_generate_receipts(self):
        """Generate property payment receipts based on wizard settings"""
        if self.number_of_receipts <= 0:
            raise ValidationError(_('Number of receipts must be positive.'))
        if self.duration <= 0:
            raise ValidationError(_('Duration must be positive.'))
        if self.amount <= 0:
            raise ValidationError(_('Amount must be positive.'))
        if self.amount < self.number_of_receipts:
            raise ValidationError(_('Amount must be greater than number of receipts'))
        
        # Calculate amount per receipt
        base_amount = self.amount // self.number_of_receipts
        remain_amount = self.amount % self.number_of_receipts
        result_lst = [base_amount] * self.number_of_receipts
        for i in range(remain_amount):
            result_lst[i] += 1
        
        # Create receipts
        receipt_vals_list = []
        current_date = self.start_date
        
        for i in range(self.number_of_receipts):
            receipt_vals = {
                'name': _('New'),
                'property_id': self.property_id.id,
                 #Although this field is related, I pass it because it doesn't investment with a form.Because i need it in create function
                'is_purchased': self.is_purchased,
                'amount': result_lst[i],
                'due_date': current_date,
            }
            receipt_vals_list.append(receipt_vals)
            
            # Calculate next date based on duration unit
            if self.duration_unit == 'day':
                current_date += timedelta(days=self.duration)
            elif self.duration_unit == 'month':
                current_date += relativedelta(months=self.duration)
            elif self.duration_unit == 'year':
                current_date += relativedelta(years=self.duration)

        # Delete existing receipts based on generation mode
        domain = [('property_id', '=', self.property_id.id)]
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
            'domain': [('property_id', '=', self.property_id.id)],
            'context': {'default_property_id': self.property_id.id,},
        }
