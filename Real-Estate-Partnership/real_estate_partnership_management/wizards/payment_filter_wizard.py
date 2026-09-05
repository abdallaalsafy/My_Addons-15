# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class PaymentFilterWizard(models.TransientModel):
    _name = 'payment.filter.wizard'
    _description = 'Payment Filter Wizard'

    # Filter Fields
    property_id = fields.Many2one('real.estate.property', string='Property')
    contact_id = fields.Many2one('real.estate.contact', string='Contact')
    payment_type = fields.Selection([
        ('purchase', 'Purchase Payment (To Seller)'),
        ('sale', 'Sale Payment (From Buyer)'),
    ], string='Payment Type')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
    ], string='Status')
    due_date_from = fields.Date(string='Due Date From')
    due_date_to = fields.Date(string='Due Date To')

    def action_filter_payments(self):
        """Open filtered payment installments list"""
        domain = []
        
        if self.property_id:
            domain.append(('property_id', '=', self.property_id.id))
        if self.contact_id:
            domain.append(('contact_id', '=', self.contact_id.id))
        if self.payment_type:
            domain.append(('payment_type', '=', self.payment_type))
        if self.status:
            domain.append(('status', '=', self.status))
        if self.due_date_from:
            # Filter by month and year only (ignore day)
            domain.append(('due_date', '>=', self.due_date_from.replace(day=1)))
        if self.due_date_to:
            # Filter by month and year only (ignore day)
            # Set to last day of the month
            if self.due_date_to.month == 12:
                last_day = self.due_date_to.replace(day=31)
            else:
                last_day = (self.due_date_to.replace(month=self.due_date_to.month + 1, day=1) - timedelta(days=1))
            domain.append(('due_date', '<=', last_day))

        action = {
            'type': 'ir.actions.act_window',
            'name': _('Payment Installments'),
            'res_model': 'real.estate.payment.installment',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': self.env.context,
        }
        
        return action
