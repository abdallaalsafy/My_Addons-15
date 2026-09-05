# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from random import randint


class RealEstateDailyCashbox(models.Model):
    _name = 'real.estate.daily.cashbox'
    _description = 'Daily Cashbox Management'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_color(self):
        return randint(1, 11)

    def _get_default_opening_balance(self):
        """Get opening balance from previous day's closing balance"""
        # Find the previous day's cashbox
        previous_cashbox = self.search([], order='date desc', limit=1)
        if previous_cashbox:
            return previous_cashbox.closing_balance

        return 0.0

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today(), tracking=True)
    color = fields.Integer(string='Color', default=lambda self: randint(1, 11))
    # Balance fields
    opening_balance = fields.Float(string='Opening Balance', required=True, tracking=True, default=_get_default_opening_balance)
    total_inflows = fields.Float(string='Total Inflows', compute='_compute_totals', store=True)
    total_outflows = fields.Float(string='Total Outflows', compute='_compute_totals', store=True)
    closing_balance = fields.Float(string='Closing Balance', compute='_compute_closing_balance', store=True)
    
    # Status and control
    status = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], default='open', required=True, tracking=True)
    
    # Additional information
    notes = fields.Text(string='Daily Notes', tracking=True)
    responsible_user = fields.Many2one('res.users', string='Cashbox Responsible User', readonly=True,
                                    default=lambda self: self.env.user, tracking=True)
    # Relations
    transaction_ids = fields.One2many('real.estate.daily.cashbox.transaction', 'cashbox_id', 
                                   string='Daily Transactions')
    transaction_count = fields.Integer(string='Transaction Count', compute='_compute_transaction_count')

    def write(self, vals):
        """Prevent modification of closed cashboxes and date changes with transactions"""
        if 'status' in vals and vals.get('status') == 'closed':
            # Allow closing
            pass
        elif self.status == 'closed':
            raise UserError(_('Cannot modify a closed cashbox.'))
        
        # Prevent date change if transactions exist
        if 'date' in vals and vals.get('date') != self.date:
            if self.transaction_ids:
                raise UserError(_('Cannot change the date of a cashbox that has transactions. Please delete the transactions first or create a new cashbox.'))
            # Also check the new date against existing cashboxes
            future_cashboxes = self.search([('date', '>', vals.get('date')), ('id', '!=', self.id)])
            if future_cashboxes:
                raise ValidationError(_('Cannot change the date to this value because there are cashboxes with later dates. Please maintain chronological order.'))

        return super(RealEstateDailyCashbox, self).write(vals)

    def unlink(self):
        """Prevent deletion of closed cashboxes"""
        if any(cashbox.status == 'closed' for cashbox in self):
            raise UserError(_('Cannot delete a closed cashbox.'))

        return super(RealEstateDailyCashbox, self).unlink()

    # ========================= Constrain Functions =================================

    @api.constrains('opening_balance')
    def _check_opening_balance(self):
        for cashbox in self:
            if cashbox.opening_balance < 0:
                raise ValidationError(_('Opening balance cannot be negative.'))

    @api.constrains('date')
    def _check_date_uniqueness(self):
        for cashbox in self:
            existing = self.search([('date', '=', cashbox.date), ('id', '!=', cashbox.id)])
            if existing:
                raise ValidationError(_('A cashbox already exists for this date.'))
            
            # Check if date is beyond today
            if cashbox.date > fields.Date.today():
                raise ValidationError(_('Cannot create a cashbox for a future date. Date must be today or in the past.'))
            
            # Check if there are any cashboxes with dates after the current date
            # This prevents creating previous dates when future dates exist
            future_cashboxes = self.search([('date', '>', cashbox.date)])
            if future_cashboxes:
                raise ValidationError(_('Cannot create a cashbox for this date because there are cashboxes with later dates. Please create cashboxes in chronological order.'))

    # ========================= Compute Functions =================================

    @api.depends('date')
    def _compute_name(self):
        for record in self:
            record.name = f"Cashbox {record.date.strftime('%Y-%m-%d')}"

    @api.depends('transaction_ids.amount', 'transaction_ids.transaction_type')
    def _compute_totals(self):
        for cashbox in self:
            inflows = sum(t.amount for t in cashbox.transaction_ids 
                         if t.transaction_type == 'inflow')
            outflows = sum(t.amount for t in cashbox.transaction_ids 
                          if t.transaction_type == 'outflow')
            cashbox.total_inflows = inflows
            cashbox.total_outflows = outflows

    @api.depends('opening_balance', 'total_inflows', 'total_outflows')
    def _compute_closing_balance(self):
        for cashbox in self:
            cashbox.closing_balance = (cashbox.opening_balance + 
                                    cashbox.total_inflows - cashbox.total_outflows)

    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        for cashbox in self:
            cashbox.transaction_count = len(cashbox.transaction_ids)

    # ========================= Action Functions =================================

    def action_close_day(self):
        """Close the day"""
        if self.status == 'closed':
            raise UserError(_('This cashbox is already closed.'))
        
        # Create closing summary
        summary = _(
            "Daily Cashbox Closing Summary:\n"
            "Opening Balance: %s\n"
            "Total Inflows: %s\n"
            "Total Outflows: %s\n"
            "Closing Balance: %s\n"
            "Total Transactions: %s"
        ) % (
            self.opening_balance,
            self.total_inflows,
            self.total_outflows,
            self.closing_balance,
            self.transaction_count
        )
        
        self.status = 'closed'

    def action_view_transactions(self):
        """View all transactions"""
        return {
            'name': _('Daily Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.daily.cashbox.transaction',
            'view_mode': 'tree,form',
            'domain': [('cashbox_id', '=', self.id)],
            'context': {'default_cashbox_id': self.id},
        }

    # def action_print_report(self):
    #     """Print daily report"""
    #     return self.env.ref('real_estate_partnership_management.action_report_daily_cashbox').report_action(self)
