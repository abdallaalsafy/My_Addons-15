# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from random import randint


class RealEstatePartner(models.Model):
    _inherit = 'res.partner'


    code = fields.Char(string='Code', required=True, copy=False, default=lambda self: _('New'))
    national_id = fields.Char(string='National ID', tracking=True)
    nickname = fields.Char(string='Nickname', tracking=True)

    is_seller = fields.Boolean(string='Seller', compute='_compute_is_seller', tracking=True, readonly=True, store=True, help="This contact can be a seller of properties")
    is_payee = fields.Boolean(string='Payee', compute='_compute_is_payee', tracking=True, readonly=True, store=True, help="This contact can receive payments for expenses")
    is_buyer = fields.Boolean(string='Buyer', compute='_compute_is_buyer', tracking=True, readonly=True, store=True, help="This contact can buy properties")
    is_partner = fields.Boolean(string='Partner', compute='_compute_is_partner', tracking=True, readonly=True, store=True, help="This contact is a partner")

    # Status and Dates
    join_date = fields.Date(string='Join Date', default=fields.Date.today, required=True, tracking=True)
    exit_date = fields.Date(string='Exit Date', tracking=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('exited', 'Exited'),
    ], string='Status', default='active', tracking=True)
    
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,
                                           readonly=True)
    current_balance = fields.Monetary(string='Current Balance', currency_field='company_currency', compute='_compute_balance', store=True)
    actual_balance = fields.Monetary(string='Actual balance', currency_field='company_currency', compute='_compute_actual_balance', store=True,
                                  help="Current balance after deducting confirmed partnerships")
    total_partnerships = fields.Monetary(string='Total partnerships', currency_field='company_currency', compute='_compute_total_partnerships', store=True)
    total_profits = fields.Monetary(string='Total Profits', currency_field='company_currency',
                                      compute='_compute_total_profit_from_sales', store=True)
    total_expenses = fields.Monetary(string='Total Expenses', currency_field='company_currency', compute='_compute_total_expenses', store=True)

    # compute fields of counts
    all_partnerships_count = fields.Integer(string='All partnerships Count', compute='_compute_all_partnership_count')
    open_partnerships_count = fields.Integer(string='Open partnerships Count', compute='_compute_opening_partnership_count')
    transaction_count = fields.Integer(string='Transaction Count', compute='_compute_transaction_count')
    profit_count = fields.Integer(string='Profit Count', compute='_compute_profit_count')
    property_purchase_count = fields.Integer(string='Property Count', compute='_compute_property_count')
    property_sale_count = fields.Integer(string='Property Count', compute='_compute_property_count')
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')

    # Related Data
    transaction_ids = fields.One2many('real.estate.transaction', 'partner_id', string='Transactions')
    partnership_ids = fields.One2many('real.estate.partnership', 'partner_id', string='partnerships')
    sale_line_ids = fields.One2many('real.estate.sale.line', 'partner_id', string='Property Sales')
    property_purchase_ids = fields.One2many('real.estate.property', 'contact_id', string='Properties Purchased', domain=[('is_purchased', '=', True)])
    property_sale_ids = fields.One2many('real.estate.property', 'contact_id', string='Properties Sold', domain=[('is_purchased', '=', False)])
    expense_ids = fields.One2many('real.estate.expense', 'contact_id', string='Expenses Paid')

    #-------------------------------
    country_id = fields.Many2one(default=lambda self: self.env.user.company_id.country_id.id)

# ============================ Built-in Functions ===============================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.partner') or _('New')
        return super(RealEstatePartner, self).create(vals_list)

# ========================= Compute Functions =================================

    @api.depends('transaction_ids.amount', 'transaction_ids.transaction_type', 'total_profits')
    def _compute_balance(self):
        for partner in self:
        # Sum all deposits, profit distributions, and partnership returns
            deposits = sum(t.amount for t in partner.transaction_ids if t.transaction_type in ['deposit','investment_return'])
        # Sum all withdrawals and expenses
            withdrawals = sum(t.amount for t in partner.transaction_ids if t.transaction_type in ['withdrawal'])
        # Calculate and set the current balance
            partner.current_balance = deposits + partner.total_profits - withdrawals

    @api.depends('current_balance', 'total_partnerships')
    def _compute_actual_balance(self):
        for partner in self:
            partner.actual_balance = partner.current_balance - partner.total_partnerships

    @api.depends('sale_line_ids.profit_amount')
    def _compute_total_profit_from_sales(self):
        """Calculate total profit from confirmed property sales for this partner"""
        for partner in self:
            total_profit = 0.0
            total_profit += sum(line.profit_amount for line in partner.sale_line_ids)
            partner.total_profits = total_profit

    @api.depends('partnership_ids.amount', 'partnership_ids.status')
    def _compute_total_partnerships(self):
        for partner in self:
            opening_partnerships_ids = partner.partnership_ids.filtered(lambda inv: inv.status == 'opening')
            partner.total_partnerships = sum(inv.down_payment for inv in opening_partnerships_ids)

    @api.depends('expense_ids.amount')
    def _compute_total_expenses(self):
        for partner in self:
            partner.total_expenses = sum(expense.amount for expense in partner.expense_ids)

# -------------------------------------------------------------
    def _compute_transaction_count(self):
        for partner in self:
            partner.transaction_count = len(partner.transaction_ids)

    def _compute_all_partnership_count(self):
        for partner in self:
            partner.all_partnerships_count = len(partner.partnership_ids)

    def _compute_opening_partnership_count(self):
            for partner in self:
                partner.open_partnerships_count = len(partner.partnership_ids.filtered(lambda inv: inv.status == 'opening'))

    def _compute_profit_count(self):
        for partner in self:
            partner.profit_count = len(partner.sale_line_ids)

    def _compute_expense_count(self):
        for partner in self:
            partner.expense_count = len(partner.expense_ids)

    def _compute_property_count(self):
        for partner in self:
            partner.property_purchase_count = len(partner.property_purchase_ids)
            partner.property_sale_count = len(partner.property_sale_ids)

# -----------------------------------------------

    @api.depends('property_sale_ids.contact_id')
    def _compute_is_seller(self):
        for partner in self:
            partner.is_seller = bool(partner.property_purchase_count)

    @api.depends('property_sale_ids.contact_id')
    def _compute_is_buyer(self):
        for contact in self:
            contact.is_buyer = bool(contact.property_sale_ids)

    @api.depends('expense_ids.contact_id')
    def _compute_is_payee(self):
        for contact in self:
            contact.is_payee = bool(contact.expense_ids)

    @api.depends('transaction_ids.partner_id', 'partnership_ids.partner_id')
    def _compute_is_partner(self):
        for partner in self:
            partner.is_partner = bool(partner.partnership_ids) or bool(partner.transaction_ids)

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
                open_partnership_count = partner.open_partnerships_count
                if open_partnership_count > 0:
                    raise UserError(
                        _('Cannot exit partner with %d active partnership(s). Please close or transfer partnerships first.')
                        % open_partnership_count
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

            if partner.partnership_ids:
                min_partnerships_date = min(partner.partnership_ids.filtered(lambda inv: inv.partnership_date).mapped('partnership_date'))
                if partner.join_date > min_partnerships_date:
                    raise UserError(_('Partner join date cannot be bigger than partnership date.'))

            if partner.transaction_ids:
                min_transaction_date = min(
                    partner.transaction_ids.filtered(lambda inv: inv.transaction_date).mapped('transaction_date'))
                if partner.join_date > min_transaction_date:
                    raise UserError(_('Partner join date cannot be bigger than transaction date.'))

            if partner.property_purchase_ids or partner.property_sale_ids:
                min_property_date = min(
                    set(partner.property_purchase_ids | partner.property_sale_ids).filtered(lambda property: property.property_date).mapped('property_date'))
                if partner.join_date > min_property_date:
                    raise UserError(_('Partner join date cannot be bigger than property date.'))

    # ========================= Action Functions =================================

    def action_create_partnership(self):
        """Open partnership form with default values for new partnership"""
        return {
            'name': _('Create New partnership'),
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.partnership',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            },
        }

    def action_create_transaction(self):
        """Open transaction form with default values for profit distribution"""
        return {
            'name': _('Create partnership Return'),
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.transaction',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            },
        }

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

    def action_view_transactions(self):
        """View partner transactions"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Transactions'),
            'res_model': 'real.estate.transaction',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id,},
        }

    def action_view_partnerships(self):
        """View partner partnerships"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner partnerships'),
            'res_model': 'real.estate.partnership',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id,},
        }

    def action_view_partner_profit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Profits'),
            'res_model': 'real.estate.sale.line',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
        }

    def action_view_purchases_properties(self):
            """View properties purchased by this contact"""
            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchases Properties'),
                'res_model': 'real.estate.property',
                'view_mode': 'tree,form',
                'domain': [('contact_id', '=', self.id), ('is_purchased', '=', True)],
                'context': {'default_contact_id': self.id, 'default_is_purchased': True},
            }
    def action_view_sale_properties(self):
        """View properties sold by this contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Properties'),
            'res_model': 'real.estate.property',
            'view_mode': 'tree,form',
            'domain': [('contact_id', '=', self.id),('is_purchased', '=', False)],
            'context': {'default_contact_id': self.id, 'default_is_purchased': False},
        }

    def action_view_expenses(self):
        """View expenses paid to this contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses Paid'),
            'res_model': 'real.estate.expense',
            'view_mode': 'tree,form',
            'domain': [('contact_id', '=', self.id)],
            'context': {'default_contact_id': self.id},
        }
    