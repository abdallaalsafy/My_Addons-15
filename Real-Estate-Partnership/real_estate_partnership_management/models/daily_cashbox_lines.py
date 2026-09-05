# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class RealEstateDailyCashboxTransaction(models.Model):
    _name = 'real.estate.daily.cashbox.transaction'
    _description = 'Daily Cashbox Transaction'
    _order = 'transaction_time desc'

    cashbox_id = fields.Many2one('real.estate.daily.cashbox', readonly=True, required=True, ondelete='cascade')
    transaction_time = fields.Datetime(string='Time', readonly=True, compute='_compute_transaction_time', store=True)
    amount = fields.Float(string='Amount', required=True)
    
    transaction_type = fields.Selection([
        ('inflow', 'Inflow'),
        ('outflow', 'Outflow'),
    ], required=True)
    
    category = fields.Selection([
        ('property_sale', 'Property Sale'),
        ('partner_deposit', 'Partner Deposit'),
        ('partner_withdrawal', 'Partner Withdrawal'),
        ('property_purchase', 'Property Purchase'),
        ('expense', 'Expense'),
        ('rent_income', 'Rent Income'),
        ('service_income', 'Service Income'),
        ('office_expenses', 'Office Expenses'),
        ('other_income', 'Other Income'),
        ('other_expense', 'Other Expense'),
    ], required=True)

    reference = fields.Char(string='Reference/Invoice')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
    ], default='cash')
    
    notes = fields.Text(string='Notes')


    def write(self, vals):
        """Prevent modification of closed cashboxes"""
        if self.cashbox_id.status == 'closed':
            raise UserError(_('Cannot modify a closed cashbox line.'))

        return super(RealEstateDailyCashboxTransaction, self).write(vals)

    def unlink(self):
        """Prevent deletion of closed cashboxes"""
        for transaction in self:
            if transaction.cashbox_id.status == 'closed':
                raise UserError(_('Cannot delete a closed cashbox line.'))

        return super(RealEstateDailyCashboxTransaction, self).unlink()

    def name_get(self):
        result = []
        for transaction in self:
            name = f"{transaction.category} - {transaction.amount} ({transaction.transaction_time})"
            result.append((transaction.id, name))
        return result

    # ========================= Constrain Functions =================================

    @api.constrains('amount')
    def _check_amount(self):
        for transaction in self:
            if transaction.amount <= 0:
                raise ValidationError(_('Transaction amount must be positive.'))

    @api.constrains('cashbox_id')
    def _check_cashbox_status(self):
        for transaction in self:
            if transaction.cashbox_id.status == 'closed':
                raise ValidationError(_('Cannot add transactions to a closed cashbox.'))

    @api.depends('cashbox_id.date')
    def _compute_transaction_time(self):
        """Compute transaction time using cashbox date and current time"""
        for transaction in self:
            if transaction.cashbox_id and transaction.cashbox_id.date:
                # Get current time
                current_time = fields.Datetime.now()
                # Combine cashbox date with current time
                cashbox_date = transaction.cashbox_id.date
                transaction_time = datetime.combine(cashbox_date, current_time.time())
                transaction.transaction_time = transaction_time
