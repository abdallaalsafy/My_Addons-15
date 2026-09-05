# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint

class RealEstateProperty(models.Model):
    _name = 'real.estate.property'
    _description = 'Real Estate property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'contract_date'

    _SELECTION_PROPERTY_TYPE = [('house', 'House'),('apartment', 'Apartment'), ('shop', 'Shop'), ('land', 'Land'),('building', 'Building'), ('villa', 'Villa'), ('office', 'Office'), ('warehouse', 'Warehouse')]
    _SELECTION_AREA_UNIT = [('meter', 'Square Meter (m²)'), ('qirat', 'Qirat'), ('unit', 'By Unit')]

    def _get_default_color(self):
        return randint(1, 11)

    @staticmethod
    def _convert_to_meters(area, unit):
        """Convert area to meters based on unit"""
        return area if unit in ['meter','unit'] else area * 175.0

    @staticmethod
    def get_available_properties_domain():
        """Get domain for available properties (not sold)"""
        return [('status', '!=', 'sold')]
    @staticmethod
    def get_available_for_sale_properties_domain():
        """Get domain for available properties (not sold)"""
        return [('status', '!=', 'sold'), ('has_any_children', '=', False)]
    @staticmethod
    def get_investment_properties_domain():
        """Get domain for properties available for investment (not sold, or child)"""
        return [('status', '!=', 'sold'), ('is_child', '=', False)]
    @staticmethod
    def get_exit_properties_domain():
        """Get domain for properties available for exit (not sold, or child)"""
        return [('status', '!=', 'sold'), ('is_child', '=', False),('total_investments', '>', 0)]


    name = fields.Char(string='Name', required=True, tracking=True, index=True)
    code = fields.Char(string='Code', required=True, copy=False, default=lambda self: _('New'), index=True)
    color = fields.Integer(string='Color', default=_get_default_color)

    # Deal Relationship
    deal_id = fields.Many2one('real.estate.deal', string='Deal', required=True,
                                help='The deal this contract is associated with (if any)',
                                domain="[('status', '!=', 'closed')]") 
    # contract Type and Classification
    property_type = fields.Selection(related='deal_id.deal_type', store=True,)
    deal_status = fields.Selection(related='deal_id.status', store=True,)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    is_purchased = fields.Boolean(string='Is Purchased')
    is_conversion = fields.Boolean(string='Is Conversioned')

    # Payment Information
    payment_method = fields.Selection([
                ('cash', 'Cash'),
                ('bank', 'Bank Transfer'),
                ('check', 'Check'),
                ('installment', 'Installment'),
            ], string='Payment Method', default='cash', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)

    # Location Information
    city_id = fields.Many2one(related='deal_id.city_id', store=True,)
    address = fields.Text(related='deal_id.address', store=True,)
    
    # contract Boundaries
    north_boundary = fields.Text(string='North Boundary', help='What borders the contract from the north')
    south_boundary = fields.Text(string='South Boundary', help='What borders the contract from the south')
    east_boundary = fields.Text(string='East Boundary', help='What borders the contract from the east')
    west_boundary = fields.Text(string='West Boundary', help='What borders the contract from the west')
    # Room Details
    built_area = fields.Float(string='Built Area', tracking=True)
    number_of_floors = fields.Integer(string='Number of Floors', tracking=True)
    total_rooms = fields.Integer(string='Total Rooms', tracking=True)
    bedrooms = fields.Integer(string='Bedrooms', tracking=True)
    bathrooms = fields.Integer(string='Bathrooms', tracking=True)
    kitchens = fields.Integer(string='Kitchens', tracking=True)
    living_rooms = fields.Integer(string='Living Rooms', tracking=True)
    
    # contract Specifications
    total_area = fields.Float(string='Total Area', required=True,  tracking=True, help='Total area of the contract (used for area ratio calculations)')
    area_unit = fields.Selection(related='deal_id.area_unit', store=True)
    # Expenses Information
    total_expenses = fields.Float(string='Total Expenses', compute='_compute_expenses', store=True)
    deal_expenses = fields.Float(string='Deal Expenses', help="""
        This field is for (Sale Contract) only.
        It get share of Sale Contract in the deal's expenses not deal's cost.
        It is calculated based on the (action confirming the sale).
        It is set to zero when it is a draft.
        The field only appears in the confirmed state.
        """)
    # Financial Information
    current_value = fields.Float(string='Current Estimated Value', tracking=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)

    # Sale & Purchase Fields
    contract_date = fields.Date(tracking=True)
    contact_id = fields.Many2one('res.partner', tracking=True,)
    contract_price = fields.Float(tracking=True,)
    down_payment = fields.Float(string='Down Payment', tracking=True, help='Down payment amount for the contract')
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_payment_remaining', store=True)
    # Profit Information
    total_profit = fields.Float(string='Total Profit', compute='_compute_financials', store=True)
    net_profit = fields.Float(string='Net Profit', compute='_compute_financials', store=True)
    management_fee_percentage = fields.Float(string='Management Fee %', default=5.0, tracking=True)
    management_fee_amount = fields.Float(string='Management Fee Amount', compute='_compute_financials', store=True)
    
    # Notes and Documents
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    
    # Relations Counts
    payment_count = fields.Integer(string='Payment Count', compute='_compute_payment_counts')
    attachment_count = fields.Integer(string='Document Count', compute='_compute_attachment_count')    
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
    profit_count = fields.Integer(string='Profit Count', compute='_compute_profit_count')

    # Related Data
    expense_ids = fields.One2many('real.estate.expense', 'contract_id', string='Expenses')
    payment_ids = fields.One2many('real.estate.payment.installment', 'contract_id', string='Payments Installment',)
    sale_line_ids = fields.One2many('real.estate.property.sale.line', 'contract_id', string='Sale Lines')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', help='Upload contract documents, images, contracts, etc.')

    # ====================== Built-in methods =================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            code = "real.estate.property.purchase" if vals.get('is_purchase') == True else "real.estate.property.sale"
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code(code) or _('New')

        properties = super(RealEstateProperty, self).create(vals_list)
        
        return properties

    def write(self, vals):
        result = super(RealEstateProperty, self).write(vals)
        return result

    def unlink(self):
        """Override unlink to add validation before deletion"""
        for contract in self:
            if contract.deal_status == 'closed':
                raise ValidationError(_('Cannot delete contract becose deal is closed.'))
            elif contract.is_purchased:
                sold_area = self.get_sum_all_sold_cotracts_area()
                if sold_area > contract.deal_id.total_area - self.total_area:
                    raise ValidationError(_('Cannot delete contract becose it sold from it.'))

            # Deleted Expense Manually Becose Deal Depend On It In Computed Fields
            contract.expense_ids.unlink() 
        return super(RealEstateProperty, self).unlink()

    # =========================== Compute Functions ===========================

    def _compute_attachment_count(self):
        for contract in self:
            contract.attachment_count = len(contract.attachment_ids)

    def _compute_expense_count(self):
        for contract in self:
            contract.expense_count = len(contract.expense_ids)

    def _compute_payment_counts(self):
        """Calculate payment counts"""
        for contract in self:
            contract.payment_count = len(contract.payment_ids)

    def _compute_profit_count(self):
        for contract in self:
            contract.profit_count = len(contract.sale_line_ids)

    #====================== Compute Calc Fields ===========================

    @api.depends('expense_ids.amount')
    def _compute_expenses(self):
        """ Calculate total confirmed or paid expenses amount"""
        for contract in self:
            contract.total_expenses = sum(exp.amount for exp in contract.expense_ids)

    @api.depends('payment_ids.amount', 'payment_ids.status', 'contract_price','down_payment')
    def _compute_payment_remaining(self):
        """Calculate payments remaining amounts"""
        for contract in self:
            installment_paid = sum(p.amount for p in contract.payment_ids if p.status == 'paid')
            contract.remaining_amount = contract.contract_price - installment_paid - contract.down_payment

    @api.depends('contract_price', 'total_expenses', 'deal_expenses')
    def _compute_total_cost(self):
        """ Calculate total cost for contract"""
        total_cost = 0
        for contract in self:
            total_cost = contract.total_expenses
            if contract.is_purchased:
                total_cost += contract.contract_price
            else:
                total_cost += contract.deal_expenses
        contract.total_cost = total_cost

    @api.depends('total_cost', 'contract_price', 'management_fee_percentage')
    def _compute_financials(self):
        for contract in self:
            if not contract.is_purchased:
                contract.total_profit = contract.contract_price - contract.total_cost
                contract.management_fee_amount = (contract.total_profit * contract.management_fee_percentage) / 100
                contract.net_profit = contract.total_profit - contract.management_fee_amount
            else:
                contract.total_profit = 0
                contract.management_fee_amount = 0
                contract.net_profit = 0

    # =========================== Constraints Functions ===========================

    @api.constrains('status')
    def _check_contact_when_confirmed_sale(self):
        for contract in self:
            if contract.status == 'draft': continue
            if not contract.contact_id:
                raise ValidationError(_('Confirmed contract must have a contact.'))

    @api.constrains('total_area', 'deal_id')
    def _check_area_for_sold_contract(self):
        for contract in self:
            if contract.is_purchased:
                continue
            sold_area = contract.get_sum_all_sold_cotracts_area()
            if contract.deal_id.total_area < sold_area + contract.total_area:
                raise ValidationError(_('All sold total area is greater than total area of deal.'))
        
    @api.constrains('total_area','contract_price', 'down_payment','status')
    def _check_area_price_payment(self):
        for contract in self:
            if contract.total_area <= 0:
                raise ValidationError(_('contract area must be greater than zero.'))

            # Check contract price
            if contract.contract_price == 0 and contract.status == 'confirmed':
                raise ValidationError(_('Contract price must be greater than zero.'))
            if contract.contract_price < 0:
                raise ValidationError(_('Contract price must be positive.'))

            # Check contract down_payment
            if contract.down_payment < 0:
                raise ValidationError(_('Down payment cannot be negative.'))
            if contract.down_payment > contract.contract_price:
                raise ValidationError(_('Down payment cannot exceed contract price.'))

    @api.constrains('contract_date', 'status')
    def _check_contract_date(self):
        """Ensure purchase date is not later than related transaction dates"""
        for contract in self:
            if contract.status == 'draft': continue

            if not contract.contract_date:
                raise ValidationError(_('Confirmed contract must have a date.'))
            
            if contract.contract_date > fields.Date.today():
                raise ValidationError(_('Contract date cannot be in the future.'))

            # Check deal date
            if contract.contract_date < contract.deal_id.open_date:
                raise ValidationError(
                    _('Cannot change contract date to %s because deal %s with open date %s is Later.'
                        'Please update expense dates first.') % 
                    (contract.contract_date, contract.deal_id.name, contract.deal_id.open_date))
        
            # Check expenses (only investment expenses) whith contract date
            for expense in contract.expense_ids:
                if expense.contract_id.is_purchased:
                    if expense.expense_date < contract.contract_date:
                        raise ValidationError(
                            _('Cannot change purchased contract date to %s because expense "%s" has date %s which is earlier. '
                            'Please update expense dates first or change contract date.') % 
                            (contract.contract_date, expense.name, expense.expense_date))
                else:
                    if expense.expense_date > contract.contract_date:
                        raise ValidationError(
                            _('Cannot change sold contract date to %s because expense "%s" has date %s which is later. '
                            'Please update expense dates first or change contract date.') % 
                            (contract.contract_date, expense.name, expense.expense_date))
                    
            # Check contract payment installments
            for payment in contract.payment_ids:
                if payment.due_date < contract.contract_date:
                    raise ValidationError(
                        _('Cannot change contract date to %s because payment "%s" has due date %s which is earlier. '
                          'Please update payment dates first.') % 
                        (contract.contract_date, payment.name, payment.due_date))

    # =========================== Action Functions ===========================

    def action_view_payments_Installments(self):
        """View payments installments for this contract"""
        action = self.env.ref('real_estate_partnership_management_pro.action_purchase_payment_installment').read()[0]
        action['domain'] = [('contract_id', '=', self.id)]
        action['context'] = {'default_contract_id': self.id,}
        return action

    def action_view_expenses(self):
        """View contract expenses"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract Expenses'),
            'res_model': 'real.estate.expense',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id,'default_expense_type': 'investment',},
        }

    def action_view_contract_profit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract Profits'),
            'res_model': 'real.estate.property.sale.line',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
        }
    
    def action_create_expense(self):
        # Open expense creation form with readonly contract field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Expense'),
            'res_model': 'real.estate.expense',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_expense_type': 'investment',
            },
        }

    def action_create_payment_installment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Purchase Installment'),
            'res_model': 'real.estate.payment.installment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
            },
        }

    def action_generate_purchase_payment_receipts(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Purchase Payment Receipts'),
            'res_model': 'purchase.payment.receipts.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
            },
        }

    def action_confirmed_sold_contract(self):
        for contract in self:
            if contract.status == 'confirmed': continue

            if contract.deal_id.total_investments_percentage < 100:
                raise ValidationError(_('Cannot confirm contract becose deal total investments percentage is less than 100.'))
                
            contract.deal_expenses = contract.get_sold_contract_deal_expense()

            vals_list = []
            for investment in contract.deal_id.investment_ids:
                partner_profit = (contract.net_profit * investment.percentage) / 100
                vals_list.append({
                    'contract_id': self.id,
                    'partner_id': investment.partner_id.id,
                    'profit_amount': partner_profit,
                })

            self.env['real.estate.property.sale.line'].create(vals_list)
            contract.status = 'confirmed'


    def action_draft_sold_contract(self):
        for contract in self:
            if contract.status == 'draft': continue

            contract.sale_line_ids.unlink()

            contract.deal_expenses = 0
            contract.status = 'draft'
        
    # ============== Logic Functions  ========================
    def get_sum_all_sold_cotracts_area(self):
        sold_area = sum(sold.total_area for sold in self.deal_id.sold_contracts_ids if sold.id != self.id)
        return sold_area

    def get_sum_confirmed_sold_cotracts_area(self):
            sold_area = sum(sold.total_area for sold in self.deal_id.sold_contracts_ids if sold.id != self.id and sold.status == 'confirmed')
            return sold_area

    def get_remaining_expenses(self,deal_id):
        sold_deal_expenses = sum(sold.deal_expenses for sold in deal_id.sold_contracts_ids)
        remaining_expenses = deal_id.total_cost_before_sold - sold_deal_expenses
        return remaining_expenses

    def get_sold_contract_deal_expense(self):
        deal_id = self.deal_id
        contract_area = self.total_area
        deal_area = deal_id.total_area

        # (1) Calculate total area of sold contract
        sold_area = self.get_sum_confirmed_sold_cotracts_area()

        # (2) Apply the new formula
        remaining_area = deal_area - sold_area
        if remaining_area > 0:
            # Calculate expense ratio based on remaining area
            expense_ratio = (contract_area / remaining_area) * 100
            # Calculate deal expenses from remaining expenses + parent profit from exits
            remaining_expenses = self.get_remaining_expenses(deal_id)
            deal_expenses = remaining_expenses * (expense_ratio / 100)
            return int(deal_expenses) # Make it as (int) because I do not want any digits
        else:
            return 0.0