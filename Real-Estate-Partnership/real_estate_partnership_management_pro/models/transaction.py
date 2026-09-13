# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint


class RealEstateTransaction(models.Model):
    _name = 'real.estate.transaction'
    _description = 'Real Estate Partner Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transaction_date desc, id desc'


    name = fields.Char(string='Transaction Reference', required=True, copy=False, default=lambda self: _('New'))

    # Relations
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True,
                                 domain="[('status', '=', 'active')]",ondelete='restrict')
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    
    # Transaction Details
    amount = fields.Monetary(string='Amount', required=True, currency_field='company_currency')
    transaction_type = fields.Selection([
        ('deposit', 'Deposit'),
        ('investment_return', 'Investment Return'),
        ('withdrawal', 'Withdrawal'),
    ], string='Transaction Type', required=True, tracking=True)
    
    transaction_date = fields.Date(string='Transaction Date', required=True, default=fields.Date.today, tracking=True)
    
    # Payment Information
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
    ], string='Payment Method', default='cash',tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    
    # Reference and Description
    description = fields.Text(string='Description', tracking=True)
    
    # Related Documents
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    # ================================= Built-in Functions =================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.transaction') or _('New')
        return super(RealEstateTransaction, self).create(vals_list)

    def write(self, vals):
        # Check if balance-affecting fields are being modified for inactive partners
        balance_affecting_fields = ['amount', 'transaction_type', 'partner_id']
        if any(field in vals for field in balance_affecting_fields):
            for transaction in self:
                if transaction.partner_id.status != 'active' or not transaction.partner_id.active:
                    raise ValidationError(_('Cannot modify transactions that affect balance for inactive partners. '
                                          'Partner "%s" is currently %s.') % 
                                        (transaction.partner_id.name, transaction.partner_id.status))
        return super(RealEstateTransaction, self).write(vals)

    def unlink(self):
        for transaction in self:
            if transaction.partner_id.status != 'active' or not transaction.partner_id.active:
                raise ValidationError(_('Cannot delete transactions that affect balance for inactive partners. '
                                      'Partner "%s" is currently %s.') %
                                    (transaction.partner_id.name, transaction.partner_id.status))
        return super(RealEstateTransaction, self).unlink()

    # =========================== Constraints Functions ===========================

    @api.constrains('transaction_date')
    def _check_date(self):
        for transaction in self:
            if transaction.transaction_date > fields.Date.today():
                raise ValidationError(_('Transaction date cannot be in the future.'))

    @api.constrains('transaction_date', 'partner_id')
    def _check_transaction_date_vs_join_date(self):
        """Ensure transaction date is not earlier than partner join date"""
        for transaction in self:
            if transaction.transaction_date and transaction.partner_id and transaction.partner_id.join_date:
                if transaction.transaction_date < transaction.partner_id.join_date:
                    raise ValidationError(_('Transaction date cannot be earlier than partner join date. '
                                          'Join date: %s, Transaction date: %s') % 
                                        (transaction.partner_id.join_date, transaction.transaction_date))

    @api.constrains('partner_id')
    def _check_partner_active(self):
        """Ensure partner is active when transaction is confirmed"""
        for transaction in self:
            if transaction.partner_id.status != 'active' or not transaction.partner_id.active:
                raise ValidationError(_('Cannot create transactions for inactive partners. '
                                        'Partner "%s" is currently %s.') %
                                      (transaction.partner_id.name, transaction.partner_id.status))

    @api.constrains('amount','transaction_type')
    def _check_amount(self):
        for transaction in self:
            # Allow negative amounts for profit distribution (losses)
            if transaction.transaction_type != 'profit_distribution' and transaction.amount <= 0:
                raise ValidationError(_('Transaction amount must be positive.'))

            if transaction.transaction_type == 'withdrawal':
                if transaction.partner_id.current_balance < 0:
                    raise ValidationError(_('Insufficient balance. Available: %s, Required: %s') %
                                          (transaction.partner_id.current_balance+transaction.amount, transaction.amount))