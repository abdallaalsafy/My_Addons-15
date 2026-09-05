# -*- coding: utf-8 -*-

"""
Real Estate Partner Model
==========================

This model manages partners in the real estate partnership management system.
Partners are individuals or entities who invest in real estate properties and share profits/losses.

Key Components:
---------------
1. **Partner Information:**
   - Basic info: name, code, phone, email, address, national_id
   - Code is auto-generated using sequence
   - Name and national_id must be unique

2. **Balance Calculation Fields:**
   - current_balance: Total balance from transactions, profits, and expenses
     Formula: (deposits + profit_distributions + investment_returns + profits_from_exits + profits_from_sales)
              - (withdrawals + expenses + expense_distributions)
   - actual_balance: Current balance after deducting confirmed investments
     Formula: current_balance - confirmed_investments_total
   - confirmed_investments_total: Sum of all confirmed investment amounts
   - total_profit_from_exits: Total profit from partner exit lines
   - total_profit_from_sales: Total profit from property sales

3. **Count Fields:**
   - investments_count: Total number of investments (all statuses)
   - confirmed_investments_count: Number of confirmed investments only
   - transaction_count: Number of transactions
   - expense_distribution_count: Number of expense distributions

4. **Status Management:**
   - active: Boolean field (can be archived)
   - status: Selection ('active', 'exited')
   - join_date: Date when partner joined the partnership
   - exit_date: Date when partner exited (set automatically on exit)

5. **Important Constraints:**
   - Cannot exit partner with active confirmed investments
   - Cannot exit partner with non-zero balance
   - Join date cannot be in the future
   - Join date cannot be later than any related record date (investments, transactions, distributions)
   - Email must be valid format
   - Phone must contain only digits
   - Name must be unique
   - National ID must be unique

6. **Related Data:**
   - transaction_ids: All financial transactions
   - investment_ids: All property investments
   - property_sale_ids: Property sale lines with profit
   - exit_line_ids: Partner exit lines with profit
   - expense_distribution_ids: Expense distributions

7. **Action Functions:**
   - action_exit_partnership: Exit partner from partnership
   - action_reactivate: Reactivate exited partner
   - action_create_transaction: Create new transaction
   - action_create_investment: Create new investment
   - action_view_transactions: View all transactions
   - action_view_investments: View all investments
   - action_view_expense_distributions: View expense distributions
   - action_view_partner_ledger: View unified ledger with running balance

8. **Tracking:**
   - All key fields are tracked for audit trail
   - Inherits mail.thread for chatter and messaging
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from random import randint


class RealEstatePartner(models.Model):
    _name = 'real.estate.partner'
    _description = 'Real Estate Partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Partner Name', required=True, tracking=True)
    code = fields.Char(string='Partner Code', required=True, copy=False, default=lambda self: _('New'))
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    address = fields.Text(string='Address', tracking=True)
    national_id = fields.Char(string='National ID', tracking=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    
    # compute fields of balance
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,
                                       readonly=True)
    current_balance = fields.Monetary(string='Current Balance', currency_field='company_currency', compute='_compute_balance', store=True)
    actual_balance = fields.Monetary(string='Actual balance', currency_field='company_currency', compute='_compute_actual_balance', store=True,
                                  help="Current balance after deducting confirmed investments")
    confirmed_investments_total = fields.Monetary(string='Investments Total', currency_field='company_currency', compute='_compute_investments_total', store=True)
    total_profit_from_exits = fields.Monetary(string='Total Profit from Partner Exits', currency_field='company_currency',
                                          compute='_compute_total_profit_from_exits', store=True)
    total_profit_from_sales = fields.Monetary(string='Total Profit from Property Sales', currency_field='company_currency',
                                      compute='_compute_total_profit_from_sales', store=True)

    # compute fields of counts
    investments_count = fields.Integer(string='Investments Count', compute='_compute_all_investment_count')
    transaction_count = fields.Integer(string='Transaction Count', compute='_compute_transaction_count')
    expense_distribution_count = fields.Integer(string='Expense Distribution Count', compute='_compute_expense_distribution_count')
    confirmed_investments_count = fields.Integer(string='Confirmed Investments Count',
                                                 compute='_compute_investments_count')

    # Status and Dates
    active = fields.Boolean(string='Active', default=True, tracking=True)
    join_date = fields.Date(string='Join Date', default=fields.Date.today, required=True, tracking=True)
    exit_date = fields.Date(string='Exit Date', tracking=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('exited', 'Exited'),
    ], string='Status', default='active', tracking=True)
    
    # Notes
    notes = fields.Text(string='Notes')
    
    # Related Data
    transaction_ids = fields.One2many('real.estate.transaction', 'partner_id', string='Transactions')
    investment_ids = fields.One2many('real.estate.property.investment', 'partner_id', string='Investments')
    property_sale_ids = fields.One2many('real.estate.property.sale.line', 'partner_id', string='Property Sales')
    exit_line_ids = fields.One2many('real.estate.partner.exit.lines', 'partner_id', string='Exit Lines')
    expense_distribution_ids = fields.One2many('real.estate.expense.distribution', 'partner_id', string='Expense Distributions')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.partner') or _('New')
        return super(RealEstatePartner, self).create(vals_list)

    # ========================= Compute Functions =================================

    @api.depends('transaction_ids.amount', 'transaction_ids.transaction_type', 'transaction_ids', 'expense_distribution_ids.partner_share', 'expense_distribution_ids.expense_id.status', 'total_profit_from_exits', 'total_profit_from_sales')
    def _compute_balance(self):
        """
        Compute the current balance for a partner based on their transactions, expense distributions, and profit from exits.
        This method calculates the current balance by summing up all confirmed deposits and profit distributions,
        adding the total profit from exits and sales, and subtracting all confirmed withdrawals, expenses, and expense distributions.
        The method is decorated with @api.depends to indicate that it should be recomputed whenever
        any of the dependent fields change.
        Args:
            self: The recordset of partners for which to compute the balance
        The method sets the current_balance field for each partner in the recordset.
        """
        for partner in self:
        # Sum all deposits, profit distributions, and investment returns
            deposits = sum(t.amount for t in partner.transaction_ids if t.transaction_type in ['deposit','profit_distribution','investment_return'])
        # Sum all withdrawals and expenses
            withdrawals = sum(t.amount for t in partner.transaction_ids if t.transaction_type in ['withdrawal','expense'])
        # Sum all expense distributions (treated as expenses)
            expense_distributions = sum(d.partner_share for d in partner.expense_distribution_ids)
        # Calculate and set the current balance
            partner.current_balance = deposits + partner.total_profit_from_exits + partner.total_profit_from_sales - withdrawals - expense_distributions

    @api.depends('current_balance', 'confirmed_investments_total')
    def _compute_actual_balance(self):
        for partner in self:
            partner.actual_balance = partner.current_balance - partner.confirmed_investments_total

    @api.depends('exit_line_ids.profit_amount')
    def _compute_total_profit_from_exits(self):
        """Calculate total profit from approved partner exit lines for this partner"""
        for partner in self:
            total_profit = 0.0
            total_profit += sum(line.profit_amount for line in partner.exit_line_ids)
            partner.total_profit_from_exits = total_profit

    @api.depends('property_sale_ids.profit_amount')
    def _compute_total_profit_from_sales(self):
        """Calculate total profit from confirmed property sales for this partner"""
        for partner in self:
            total_profit = 0.0
            total_profit += sum(line.profit_amount for line in partner.property_sale_ids)
            partner.total_profit_from_sales = total_profit

    @api.depends('investment_ids.amount', 'investment_ids.status')
    def _compute_investments_total(self):
        for partner in self:
            confirmed_investments = partner.investment_ids.filtered(lambda inv: inv.status == 'confirmed')
            partner.confirmed_investments_total = sum(inv.amount for inv in confirmed_investments)

    def _compute_investments_count(self):
        for partner in self:
            partner.confirmed_investments_count = len(partner.investment_ids.filtered(lambda inv: inv.status == 'confirmed'))

    def _compute_transaction_count(self):
        for partner in self:
            partner.transaction_count = len(partner.transaction_ids)

    def _compute_all_investment_count(self):
        for partner in self:
            partner.investments_count = len(partner.investment_ids)

    def _compute_expense_distribution_count(self):
        for partner in self:
            partner.expense_distribution_count = len(partner.expense_distribution_ids)

#========================= Constrain Functions =================================

    @api.constrains('email')
    def _check_email(self):
        for partner in self:
            if partner.email and '@' not in partner.email:
                raise ValidationError(_('Please enter a valid email address.'))

    @api.constrains('phone')
    def _check_phone(self):
        for partner in self:
            if partner.phone and not partner.phone.replace(' ', '').replace('-', '').isdigit():
                raise ValidationError(_('Phone number should contain only digits.'))

    @api.constrains('name')
    def _check_unique_name(self):
        for partner in self:
            if partner.name:
                existing = self.search([('name', '=ilike', partner.name), ('id', '!=', partner.id)])
                if existing:
                    raise ValidationError(_('Partner name must be unique. A partner with this name already exists.'))

    @api.constrains('national_id')
    def _check_unique_national_id(self):
        for partner in self:
            if partner.national_id:
                existing = self.search([('national_id', '=', partner.national_id), ('id', '!=', partner.id)])
                if existing:
                    raise ValidationError(_('National ID must be unique. A partner with this National ID already exists.'))

    @api.constrains('status','active')
    def _check_partner_status(self):
        for partner in self:
            if partner.status == 'exited' or not partner.active:
                investment_count = partner.confirmed_investments_count
                if investment_count > 0:
                    raise UserError(
                        _('Cannot exit partner with %d active investment(s). Please close or transfer investments first.')
                        % investment_count
                    )

                if partner.current_balance != 0:
                    raise UserError(_('Cannot exit partner with balance. Please withdraw balance first.'))

    @api.constrains('join_date')
    def _check_partner_join_date(self):
        for partner in self:
            if not partner.join_date:
                continue

            if partner.join_date and partner.join_date > fields.Date.today():
                raise ValidationError(_('Partner join date cannot be in the future.'))

            if partner.investment_ids:
                min_investments_date = min(partner.investment_ids.filtered(lambda inv: inv.investment_date).mapped('investment_date'))
                if partner.join_date > min_investments_date:
                    raise UserError(_('Partner join date cannot be bigger than investment date.'))

            if partner.transaction_ids:
                min_transaction_date = min(
                    partner.transaction_ids.filtered(lambda inv: inv.transaction_date).mapped('transaction_date'))
                if partner.join_date > min_transaction_date:
                    raise UserError(_('Partner join date cannot be bigger than transaction date.'))

            if partner.expense_distribution_ids:
                min_distribution_date = min(
                    partner.expense_distribution_ids.filtered(lambda inv: inv.distribution_date).mapped('distribution_date'))
                if partner.join_date > min_distribution_date:
                    raise UserError(_('Partner join date cannot be bigger than distribution date.'))

    # ========================= Action Functions =================================

    def action_exit_partnership(self):
        """Exit partner from partnership"""
        self.write({
            'status': 'exited',
            'exit_date': fields.Date.today(),
        })

    def action_reactivate(self):
        """Reactivate exited partner"""
        self.write({
            'status': 'active',
            'exit_date': False,
            'active': True,
        })

    def action_create_transaction(self):
        """Open transaction form with default values for profit distribution"""
        return {
            'name': _('Create Investment Return'),
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.transaction',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'readonly_partner_id': True,
            },
        }

    def action_create_investment(self):
        """Open investment form with default values for new investment"""
        return {
            'name': _('Create New Investment'),
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.property.investment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'readonly_partner_id': True,
            },
        }

    def action_view_transactions(self):
        """View partner transactions"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Transactions'),
            'res_model': 'real.estate.transaction',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id,'readonly_partner_id': True,},
        }

    def action_view_investments(self):
        """View partner investments"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Investments'),
            'res_model': 'real.estate.property.investment',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id,'readonly_partner_id': True,},
        }

    def action_view_expense_distributions(self):
        """View partner expense distributions"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Expense Distributions'),
            'res_model': 'real.estate.expense.distribution',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
        }

    def action_view_partner_ledger(self):
        """Open partner unified ledger (all transactions with running balance)"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Ledger'),
            'res_model': 'partner.unified.ledger',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }