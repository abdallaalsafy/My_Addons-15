# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from random import randint


class RealEstateExpense(models.Model):
    _name = 'real.estate.expense'
    _description = 'Real Estate Property Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expense_date'

    _SELECTION_PAYMENT_METHOD = [('cash', 'Cash'),('bank', 'Bank Transfer'),('check', 'Check'),('credit_card', 'Credit Card'),]

    def _get_default_color(self):
        return randint(1, 11)

    def _get_available_properties_domain(self):
        """Return domain for available properties for investment expenses"""
        return [('deal_id', '=', self.deal_id), ('status', '!=', 'sold')]

    name = fields.Char(string='Expense Description', required=True, tracking=True)
    code = fields.Char(string='Expense Code', required=True, copy=False, default=lambda self: _('New'))
    color = fields.Integer(string='Color', default=_get_default_color)

    expense_type = fields.Selection([
        ('investment', 'Investment Expense'),
        ('company', 'Company Expense'),
    ], string='Expense Type', required=True, tracking=True)
    status = fields.Selection([
            ('confirmed', 'Confirmed'),
            ('paid', 'Paid'),
            ], string='Status', default='confirmed', tracking=True)

    amount = fields.Float(string='Expense Amount', required=True, tracking=True)
    expense_date = fields.Date(string='Expense Date', required=True, default=fields.Date.today, tracking=True)
    
    # Relations
    deal_id = fields.Many2one('real.estate.deal', string='Deal', tracking=True, index=True, ondelete='cascade',
                              domain="[('status', '=', 'opening')]", 
                              help="Select the deal associated with this expense (for investment expenses only)")
    contract_id = fields.Many2one('real.estate.property', string='Contract', tracking=True, index=True, ondelete='cascade',
                                 domain=[('deal_status','=','opening')],)
    category_id = fields.Many2one('real.estate.expense.category', string='Expense Category', 
                                 required=True, tracking=True, ondelete='restrict')
    
    # Payment Information
    contact_id = fields.Many2one('res.partner', string='Paid To', tracking=True,ondelete='restrict')
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
        if 'deal_id' in vals or 'contract_id' in vals or 'expense_type' in vals:
            amount = 0
        elif 'amount' in vals:
            amount = vals['amount']
        self.validation_on_create_delete(delete=True,amount=amount)

        rtn = super(RealEstateExpense, self).write(vals)

        if 'deal_id' in vals or 'contract_id' in vals or 'expense_type' in vals:
            self.validation_on_create_delete()

        return rtn

    def unlink(self):
        self.validation_on_create_delete(delete=True)

        return super(RealEstateExpense, self).unlink()
    # =========================== OnChange Functions ===========================

    @api.onchange('expense_type')
    def _onchange_expense_type(self):
        for expense in self:
            expense.deal_id = False
            expense.contract_id = False
            
    # =========================== Constraints Functions ===========================

    @api.constrains('amount')
    def _check_amount(self):
        for expense in self:
            if expense.amount <= 0:
                raise ValidationError(_('Expense amount must be positive.'))

    @api.constrains('expense_date', 'deal_id', 'contract_id')
    def _check_date(self):
        for expense in self:
            if expense.expense_date > fields.Date.today():
                raise ValidationError(_('Expense date cannot be in the future.'))

            if expense.expense_type == 'investment' and expense.deal_id:
                if expense.expense_date < expense.deal_id.open_date:
                    raise ValidationError(_('Expense date cannot be earlier than deal open date. '
                                            'Deal open date: %s, Expense date: %s') % 
                                        (expense.deal_id.open_date, expense.expense_date))

            if expense.expense_type == 'investment' and expense.contract_id and expense.contract_id.contract_date:
                if expense.contract_id.is_purchased:
                    if expense.expense_date < expense.contract_id.contract_date:
                        raise ValidationError(_('Expense date cannot be earlier than purchased contract date. '
                                                'Purchased contract date: %s, Expense date: %s') % 
                                            (expense.contract_id.contract_date, expense.expense_date))
                else:
                    if expense.expense_date > expense.contract_id.contract_date:
                        raise ValidationError(_('Expense date cannot be earlier than sold contract date. '
                                                'Sold contract date: %s, Expense date: %s') % 
                                            (expense.contract_id.contract_date, expense.expense_date))

    # =========================== Action Functions ===========================
    def action_mark_paid(self):
        """Mark expense as paid and distribute among partners if it's a company expense"""
        self.status = 'paid'

    # =========================== Other Functions ===========================
     
    def validation_on_create_delete(self, delete=False,amount=0):
        for expense in self:
            if expense.expense_type == 'company': continue

            deal_id = expense.deal_id if expense.deal_id else expense.contract_id.deal_id
            deal_status = deal_id.status

            if deal_status != 'opening':
                raise UserError(_('Cannot create an expense for a deal that is not in opening status.'))

            if expense.contract_id and expense.contract_id.is_purchased == False and expense.contract_id.status != 'draft':
                raise UserError(_('Cannot create an expense for a sold contract that is not in draft status.'))


            if deal_id.remaining_area == 0 and deal_id.draft_sold_contracts_count == 0: 
                raise UserError(_('Cannot create an expense for a deal that has no remaining area and no draft sold contracts.'))

            #----------------------------------
            if ((expense.contract_id and expense.contract_id.is_purchased == True) or expense.deal_id) and delete:
                expense_amunt = expense.amount - amount
                remaining_expenses = self.env['real.estate.property'].get_remaining_expenses(deal_id)
                if remaining_expenses < expense_amunt:
                    raise UserError(_('Cannot delete an expense that exceeds the remaining expenses.'))
