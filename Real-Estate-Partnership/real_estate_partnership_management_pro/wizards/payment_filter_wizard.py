# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class PaymentFilterWizard(models.TransientModel):
    _name = 'payment.filter.wizard'
    _description = 'Payment Filter Wizard'

    # Filter Fields
    contract_id = fields.Many2one('real.estate.property', string='Property')
    contact_id = fields.Many2one('res.partner', string='Contact')
    payment_type = fields.Selection([
        ('purchase', 'Purchase Payment (To Saller)'),
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
        
        if self.contract_id:
            domain.append(('contract_id', '=', self.contract_id.id))
        if self.contact_id:
            domain.append(('contact_id', '=', self.contact_id.id))
        if self.payment_type:
            is_purchased = True if self.payment_type == 'purchase' else False
            domain.append(('is_purchased', '=', is_purchased))
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
