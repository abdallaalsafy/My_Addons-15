# -*- coding: utf-8 -*-

"""
Real Estate Expense Model
==========================

This model manages expenses in the real estate partnership management system.
Expenses represent costs incurred either for property investments or company operations.

Key Components:
---------------
1. **Expense Information:**
   - Basic info: name, code, amount, expense_date
   - Code is auto-generated using sequence
   - Expense date cannot be in the future

2. **Expense Types:**
   - investment: Property-related expenses (investments)
   - company: Company operational expenses shared among partners

3. **Expense Distribution:**
   - For investment expenses: Linked to a specific property
   - For company expenses: Distributed among selected partners or all active partners
   - Distribution methods: percentage (based on partner balance) or equal
   - distribution_ids: One2many relation to expense distribution records

4. **Distribution Options:**
   - all_partners: If checked, expense distributed among all active company partners
   - partner_ids: Specific partners to distribute expense among (for company expenses)
   - distribution_method: How to calculate partner shares (percentage or equal)

5. **Payment Information:**
   - paid_to_contact_id: Contact/person who received payment
   - payment_method: Cash, Bank Transfer, Check, Credit Card
   - payment_reference: Reference number for the payment

6. **Status Management:**
   - confirmed: Expense is confirmed but not yet paid
   - paid: Expense has been paid and distributed

7. **Important Constraints:**
   - Expense amount must be positive
   - Expense date cannot be in the future
   - Investment expenses must have a property specified
   - Investment expense date cannot be earlier than property purchase date
   - Cannot edit/delete property expenses for sold properties
   - Company expenses can only be distributed among active partners

8. **Related Data:**
   - property_id: Property for investment expenses
   - partner_ids: Partners for company expenses
   - distribution_ids: Partner distribution records
   - category_id: Expense category
   - attachment_ids: Supporting documents

9. **Action Functions:**
   - action_mark_paid: Mark expense as paid and trigger distribution

10. **Tracking:**
    - All key fields are tracked for audit trail
    - Inherits mail.thread for chatter and messaging
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from random import randint


class RealEstateExpense(models.Model):
    _name = 'real.estate.expense'
    _description = 'Real Estate Property Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expense_date desc'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Expense Description', required=True, tracking=True)
    code = fields.Char(string='Expense Code', required=True, copy=False, default=lambda self: _('New'))
    color = fields.Integer(string='Color', default=_get_default_color)
    
    # Expense Type
    expense_type = fields.Selection([
        ('investment', 'Expense'),
        ('company', 'Company Expense'),
    ], string='Expense Type', required=True, default='investment', tracking=True)
    
    # Relations
    property_id = fields.Many2one('real.estate.property', string='Property', tracking=True, index=True,
                                 domain=lambda self: self.env['real.estate.property'].get_available_properties_domain(),ondelete='cascade')
    partner_ids = fields.Many2many('real.estate.partner', string='Split Among Partners', tracking=True, index=True,
                                   help="Select partners to split this expense among (for company expenses only)",ondelete='restrict')
    
    # Distribution Options
    all_partners = fields.Boolean(string='All Company Partners', default=False, tracking=True,
                                  help="If checked, expense will be distributed among all active company partners")
    distribution_method = fields.Selection([
        ('percentage', 'Percentage'),
        ('equal', 'Equally'),
    ], string='Distribution Method', default='percentage', tracking=True,
       help="How to distribute expense among partners")
    # Expense Detailsinvestment
    amount = fields.Float(string='Expense Amount', required=True, tracking=True)
    expense_date = fields.Date(string='Expense Date', required=True, default=fields.Date.today, tracking=True)
    
    # Expense Categories
    category_id = fields.Many2one('real.estate.expense.category', string='Expense Category', 
                                 required=True, tracking=True, ondelete='restrict')
    
    # Payment Information
    paid_to_contact_id = fields.Many2one('real.estate.contact', string='Paid To', tracking=True,ondelete='restrict')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
    ], string='Payment Method',default='cash', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    
    # Status
    status = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
    ], string='Status', default='confirmed', tracking=True)
    
    # Documents and Notes
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    notes = fields.Text(string='Notes')
    
    # Expense Distributions
    distribution_ids = fields.One2many('real.estate.expense.distribution', 'expense_id', string='Partner Distributions',readonly=True)

    # =========================== Built-in Functions ===========================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.expense') or _('New')
        
        expenses = super(RealEstateExpense, self).create(vals_list)

        for record in expenses:
            if record.expense_type == 'company':
                record.distribute_company_expense()

        return expenses

    def write(self, vals):
        # Validate property and partners for investment expenses
        expense_affecting_fields = ['amount', 'distribution_method', 'partner_ids','property_id']
        if any(field in vals for field in expense_affecting_fields):
            for expense in self:
                if expense.expense_type == 'investment':
                    self.validate_property_for_expense(expense.property_id)
                else:
                    for partner in expense.partner_ids:
                        self.validate_partner_for_expense(partner)

        rtn = super(RealEstateExpense, self).write(vals)

        for expense in self:
            if expense.expense_type == 'company':
                expense.distribute_company_expense()

        return rtn

    def unlink(self):
        # Prevent deleting property expenses if property is sold
        for expense in self:
            if expense.expense_type == 'investment':
                self.validate_property_for_expense(expense.property_id)
            else:
                for partner in expense.partner_ids:
                    self.validate_partner_for_expense(partner)

            # Because Partner need distribution_ids in compute Field
            # Because this line compute field cannot be computedS
            expense.distribution_ids.unlink()
        return super(RealEstateExpense, self).unlink()

    # =========================== Onchange Functions ===========================

    @api.onchange('all_partners')
    def _onchange_all_partners(self):
        """Fill partner_ids with all active partners when all_partners is checked"""
        if self.all_partners:
            # Get all active partners
            active_partners = self.env['real.estate.partner'].search([('status', '=', 'active')])
            self.partner_ids = active_partners

    # =========================== Constraints Functions ===========================

    @api.constrains('amount')
    def _check_amount(self):
        for expense in self:
            if expense.amount <= 0:
                raise ValidationError(_('Expense amount must be positive.'))

    @api.constrains('expense_date')
    def _check_date(self):
        for expense in self:
            if expense.expense_date > fields.Date.today():
                raise ValidationError(_('Expense date cannot be in the future.'))

    @api.constrains('expense_date', 'property_id')
    def _check_expense_date_property_purchase_date(self):
        """Ensure expense date is not earlier than property purchase date"""
        for expense in self:
            if expense.expense_type == 'investment' and expense.expense_date and expense.property_id and expense.property_id.purchase_date:
                if expense.expense_date < expense.property_id.purchase_date:
                    raise ValidationError(_('Expense date cannot be earlier than property purchase date. '
                                          'Purchase date: %s, Expense date: %s') % 
                                        (expense.property_id.purchase_date, expense.expense_date))

    @api.constrains('property_id')
    def _check_property_status(self):
        for expense in self:
            if expense.property_id:
                self.validate_property_for_expense(expense.property_id)

    @api.constrains('property_id', 'partner_ids', 'expense_type')
    def _check_expense_type(self):
        for expense in self:
            if expense.expense_type == 'investment':
                if not expense.property_id:
                    raise ValidationError(_('Investment expenses must have a property specified.'))
                if expense.partner_ids:
                    raise ValidationError(_('Investment expenses cannot have partners specified.'))
            elif expense.expense_type == 'company':
                if expense.property_id:
                    raise ValidationError(_('Company expenses cannot have a property specified.'))
                if expense.partner_ids:
                    for partner in expense.partner_ids:
                        self.validate_partner_for_expense(partner)
    # =========================== Validation Functions ===========================

    @staticmethod
    def validate_property_for_expense(property):
        """
        Validate if property can accept new expense
        Raises ValidationError if property cannot accept expense
        """
        if property.status == 'sold':
            raise ValidationError(_('Cannot create expenses for sold properties.'))

    @staticmethod
    def validate_partner_for_sale(partner):
        """
        Validate if partner can accept new expense
        Raises ValidationError if partner cannot accept expense
        """
        if partner.status != 'active' or not partner.active:
            raise ValidationError(_('Cannot create company expense: partner "%s" is not active.') % partner.name)

    # =========================== Action Functions ===========================
    def action_mark_paid(self):
        """Mark expense as paid and distribute among partners if it's a company expense"""
        self.status = 'paid'

    def action_redistribute(self):
        """Manually redistribute company expense among partners"""
        self.ensure_one()

        if self.expense_type != 'company':
            raise UserError(_('Redistribution is only available for company expenses.'))

        # Validate partners
        for partner in self.partner_ids:
            self.validate_partner_for_expense(partner)

        self.distribute_company_expense()
    # =========================== Helper Functions ===========================

    def distribute_company_expense(self):
        """Distribute company expense among partners based on settings"""
        # Get partners to distribute expense among
        partners = self.partner_ids

        # Remove old distributions
        self.distribution_ids.unlink()

        if partners:
            # Calculate and distribute shares based on method
            if self.distribution_method == 'percentage':
                self._distribute_by_percentage(partners)
            else:  # equal
                self._distribute_equally(partners)

    def _distribute_by_percentage(self, partners):
        """Distribute expense among partners based on their balance percentage"""
        def _get_partner_balance(partner):
            if partner.actual_balance >= 0:
                return partner.current_balance
            elif partner.current_balance >= 0:
                return partner.confirmed_investments_total
            return abs(partner.actual_balance)

        # Calculate total balance
        total_balance = sum(_get_partner_balance(partner) for partner in partners)

        if not total_balance:
            return

        distribution_vals = []

        for partner in partners:
            balance = _get_partner_balance(partner)

            balance_percentage = balance / total_balance
            partner_share = self.amount * balance_percentage

            distribution_vals.append({
                'expense_id': self.id,
                'partner_id': partner.id,
                'partner_share': partner_share,
                'share_percentage': balance_percentage,
                'calculation_basis': balance,
            })

        self.env['real.estate.expense.distribution'].create(distribution_vals)

    def _distribute_equally(self, partners):
        """Distribute expense equally among partners"""
        # Calculate equal share
        equal_share = self.amount / len(partners)

        for partner in partners:
            # Create expense distribution record
            self.env['real.estate.expense.distribution'].create({
                'expense_id': self.id,
                'partner_id': partner.id,
                'partner_share': equal_share,
                'share_percentage': 1 / len(partners),
            })