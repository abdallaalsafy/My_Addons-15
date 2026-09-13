# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from random import randint


class RealEstateExpense(models.Model):
    _name = 'real.estate.expense'
    _description = 'Real Estate Property & Company Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expense_date'

    _SELECTION_PAYMENT_METHOD = [('cash', 'Cash'),('bank', 'Bank Transfer'),('check', 'Check'),('credit_card', 'Credit Card'),]

    name = fields.Char(string='Expense Description', required=True, tracking=True)
    code = fields.Char(string='Expense Code', required=True, copy=False, default=lambda self: _('New'))

    expense_type = fields.Selection([
        ('investment', 'Investment Expense'),
        ('company', 'Company Expense'),
    ], string='Expense Type', required=True, tracking=True)
    status = fields.Selection([
            ('confirmed', 'Confirmed'),
            ('paid', 'Paid'),
            ], string='Status', default='confirmed', tracking=True)

    amount = fields.Monetary(string='Expense Amount', required=True, currency_field='company_currency', tracking=True)
    expense_date = fields.Date(string='Expense Date', required=True, default=fields.Date.today, tracking=True)
    
    # Relations
    investment_id = fields.Many2one('real.estate.investment', string='investment', tracking=True, index=True, ondelete='cascade',
                              domain="[('status', '=', 'opening')]", 
                              help="Select the investment associated with this expense (for investment expenses only)")
    property_id = fields.Many2one('real.estate.property', string='Property', tracking=True, index=True, ondelete='cascade',
                                 domain=[('investment_status','=','opening')],)
    category_id = fields.Many2one('real.estate.expense.category', string='Expense Category', 
                                 required=True, tracking=True, ondelete='restrict')
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    
    # Payment Information
    paid_date = fields.Date(string='Paid Date', tracking=True)
    payment_method = fields.Selection(_SELECTION_PAYMENT_METHOD, string='Payment Method',default='cash', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    
    notes = fields.Text(string='Notes')
    
    # Relations Data
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    # =========================== Built-in Functions ===========================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            code = "real.estate.expense.investment" if vals.get('expense_type') == 'investment' else "real.estate.expense.company"
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code(code) or _('New')

        expenses = super(RealEstateExpense, self).create(vals_list)

        expenses.validation_on_create_delete()
                        
        return expenses

    def write(self, vals):
        amount = vals['amount'] if 'amount' in vals else 0
        self.validation_on_create_delete(delete=True,amount=amount)

        rtn = super(RealEstateExpense, self).write(vals)

        if 'investment_id' in vals or 'property_id' in vals or 'expense_type' in vals:
            self.validation_on_create_delete()

        return rtn

    def unlink(self):
        self.validation_on_create_delete(delete=True)

        return super(RealEstateExpense, self).unlink()
    # =========================== OnChange Functions ===========================

    @api.onchange('expense_type')
    def _onchange_expense_type(self):
        for expense in self:
            expense.investment_id = False
            expense.property_id = False
            
    # =========================== Constraints Functions ===========================

    @api.constrains('amount')
    def _check_amount(self):
        for expense in self:
            if expense.amount <= 0:
                raise ValidationError(_('Expense amount must be positive.'))

    @api.constrains('paid_date')
    def _check_paid_date(self):
        for expense in self:
            if expense.paid_date and expense.paid_date < expense.expense_date:
                raise ValidationError(_('Paid date cannot be earlier than expense date.'))

    @api.constrains('expense_date', 'investment_id', 'property_id')
    def _check_date(self):
        for expense in self:
            if expense.expense_date > fields.Date.today():
                raise ValidationError(_('Expense date cannot be in the future.'))

            if expense.expense_type == 'investment' and expense.investment_id:
                if expense.expense_date < expense.investment_id.open_date:
                    raise ValidationError(_('Expense date cannot be earlier than investment open date. '
                                            'investment open date: %s, Expense date: %s') % 
                                        (expense.investment_id.open_date, expense.expense_date))

            if expense.expense_type == 'investment' and expense.property_id and expense.property_id.property_date:
                if expense.property_id.is_purchased:
                    if expense.expense_date < expense.property_id.property_date:
                        raise ValidationError(_('Expense date cannot be earlier than purchased property date. '
                                                'Purchased property date: %s, Expense date: %s') % 
                                            (expense.property_id.property_date, expense.expense_date))
                else:
                    if expense.expense_date > expense.property_id.property_date:
                        raise ValidationError(_('Expense date cannot be earlier than sold property date. '
                                                'Sold property date: %s, Expense date: %s') % 
                                            (expense.property_id.property_date, expense.expense_date))

    # =========================== Action Functions ===========================
    def action_mark_paid(self):
        """Mark expense as paid and distribute among partners if it's a company expense"""
        self.write({'status': 'paid', 'paid_date': fields.Date.today()})

    def action_mark_unpaid(self):
        """Mark expense as unpaid"""
        self.write({'status': 'confirmed', 'paid_date': False})

    # =========================== Other Functions ===========================
     
    def validation_on_create_delete(self, delete=False,amount=0):
        for expense in self:
            if expense.expense_type == 'company': continue

            investment_id = expense.investment_id if expense.investment_id else expense.property_id.investment_id
            investment_status = investment_id.status

            if investment_status != 'opening':
                raise UserError(_('Cannot create an expense for a investment that is not in opening status.'))

            if expense.property_id and expense.property_id.is_purchased == False and expense.property_id.status != 'draft':
                raise UserError(_('Cannot create an expense for a sold property that is not in draft status.'))


            if investment_id.remaining_area == 0 and investment_id.draft_sold_properties_count == 0: 
                raise UserError(_('Cannot create an expense for a investment that has no remaining area and no draft sold properties.'))

            #----------------------------------
            if ((expense.property_id and expense.property_id.is_purchased == True) or expense.investment_id) and delete:
                expense_amunt = expense.amount - amount
                remaining_expenses = self.env['real.estate.property'].get_remaining_expenses(investment_id)
                if remaining_expenses < expense_amunt:
                    raise UserError(_('Cannot delete an expense that exceeds the remaining expenses.'))
