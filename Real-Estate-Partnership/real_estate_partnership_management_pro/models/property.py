# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .expense import RealEstateExpense as exepenseSL


class RealEstateProperty(models.Model):
    _name = 'real.estate.property'
    _description = 'Real Estate Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'property_date'

    _SELECTION_PROPERTY_TYPE = [('house', 'House'),('apartment', 'Apartment'), ('shop', 'Shop'), ('land', 'Land'),('building', 'Building'), ('villa', 'Villa'), ('office', 'Office'), ('warehouse', 'Warehouse')]
    _SELECTION_AREA_UNIT = [('meter', 'Square Meter (m²)'), ('qirat', 'Qirat'), ('unit', 'By Unit')]


    name = fields.Char(string='Name', required=True, tracking=True, index=True)
    code = fields.Char(string='Code', required=True, copy=False, default=lambda self: _('New'), index=True)

    # Investment Relationship
    investment_id = fields.Many2one('real.estate.investment', string='Investment', required=True,
                                help='The investment this property is associated with',
                                domain="[('status', '!=', 'closed')]")
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)

    # Property Type and Classification
    property_type = fields.Selection(related='investment_id.investment_type', store=True,)
    investment_status = fields.Selection(related='investment_id.status', store=True,)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    is_purchased = fields.Boolean(string='Is Purchased')
    is_conversion = fields.Boolean(string='Is Conversioned')

    # Payment Information
    payment_method = fields.Selection(exepenseSL._SELECTION_PAYMENT_METHOD, string='Payment Method', default='cash', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)

    # Location Information
    city_id = fields.Many2one(related='investment_id.city_id', store=True,)
    address = fields.Text(related='investment_id.address', store=True,)
    
    # Property Boundaries
    north_boundary = fields.Text(string='North Boundary', help='What borders the property from the north?')
    south_boundary = fields.Text(string='South Boundary', help='What borders the property from the south?')
    east_boundary = fields.Text(string='East Boundary', help='What borders the property from the east?')
    west_boundary = fields.Text(string='West Boundary', help='What borders the property from the west?')
    # Room Details
    built_area = fields.Float(string='Built Area', tracking=True)
    number_of_floors = fields.Integer(string='Number of Floors', tracking=True)
    total_rooms = fields.Integer(string='Total Rooms', tracking=True)
    bedrooms = fields.Integer(string='Bedrooms', tracking=True)
    bathrooms = fields.Integer(string='Bathrooms', tracking=True)
    kitchens = fields.Integer(string='Kitchens', tracking=True)
    living_rooms = fields.Integer(string='Living Rooms', tracking=True)
    
    # Property Specifications
    total_area = fields.Float(string='Total Area', required=True,  tracking=True, help='Total area of the property (used for area ratio calculations)')
    area_unit = fields.Selection(related='investment_id.area_unit', store=True)
    # Expenses Information
    total_expenses = fields.Monetary(string='Total Expenses', compute='_compute_expenses', store=True, currency_field='company_currency')
    investment_expenses = fields.Monetary(string='Investment Expenses', currency_field='company_currency', help="""
        This field is for (Sale Property) only.
        It get share of Sale Property in the investment's expenses not investment's cost.
        It is calculated based on the (action confirming the sale).
        It is set to zero when it is a draft.
        The field only appears in the confirmed state.
        """)
    # Financial Information
    current_value = fields.Monetary(string='Current Estimated Value', tracking=True, currency_field='company_currency')
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_total_cost', store=True, currency_field='company_currency')

    # Sale & Purchase Fields
    property_date = fields.Date(tracking=True)
    contact_id = fields.Many2one('res.partner', tracking=True,)
    property_price = fields.Monetary(string='Property Price', tracking=True, currency_field='company_currency')
    down_payment = fields.Monetary(string='Down Payment', tracking=True, currency_field='company_currency', help='Down payment amount for the property')
    remaining_amount = fields.Monetary(string='Remaining', compute='_compute_payment_remaining', store=True, currency_field='company_currency')
    # Profit Information
    total_profit = fields.Monetary(string='Total Profits', compute='_compute_financials', store=True, currency_field='company_currency')
    net_profit = fields.Monetary(string='Net Profit', compute='_compute_financials', store=True, currency_field='company_currency')
    management_fee_percentage = fields.Float(string='Management Fee %', default=5.0, tracking=True)
    management_fee_amount = fields.Monetary(string='Management Fee Amount', compute='_compute_financials', store=True, currency_field='company_currency')

    # Notes and Documents
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    
    # Relations Counts
    payment_count = fields.Integer(string='Payment Count', compute='_compute_payment_counts')
    attachment_count = fields.Integer(string='Document Count', compute='_compute_attachment_count')    
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
    profit_count = fields.Integer(string='Profit Count', compute='_compute_profit_count')

    # Related Data
    expense_ids = fields.One2many('real.estate.expense', 'property_id', string='Expenses')
    payment_ids = fields.One2many('real.estate.payment.installment', 'property_id', string='Payments Installment',)
    sale_line_ids = fields.One2many('real.estate.sale.line', 'property_id', string='Sale Lines')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', help='Upload property documents, images, properties, etc.')

    # ====================== Built-in methods =================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            code = "real.estate.property.purchase" if vals.get('is_purchased') == True else "real.estate.property.sale"
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code(code) or _('New')

        properties = super(RealEstateProperty, self).create(vals_list)
        
        return properties

    def write(self, vals):
        result = super(RealEstateProperty, self).write(vals)
        return result

    def unlink(self):
        """Override unlink to add validation before deletion"""
        for property in self:
            if property.investment_status == 'closed':
                raise ValidationError(_('Cannot delete property becose investment is closed.'))
            elif property.is_purchased:
                sold_area = self.get_sum_all_sold_properties_area()
                if sold_area > property.investment_id.total_area - self.total_area:
                    raise ValidationError(_('Cannot delete property becose it sold from it.'))

            # Deleted Expense Manually Becose investment Depend On It In Computed Fields
            property.expense_ids.unlink() 
        return super(RealEstateProperty, self).unlink()

    # =========================== Compute Functions ===========================

    def _compute_attachment_count(self):
        for property in self:
            property.attachment_count = len(property.attachment_ids)

    def _compute_expense_count(self):
        for property in self:
            property.expense_count = len(property.expense_ids)

    def _compute_payment_counts(self):
        """Calculate payment counts"""
        for property in self:
            property.payment_count = len(property.payment_ids)

    def _compute_profit_count(self):
        for property in self:
            property.profit_count = len(property.sale_line_ids)

    #====================== Compute Calc Fields ===========================

    @api.depends('expense_ids.amount')
    def _compute_expenses(self):
        """ Calculate total confirmed or paid expenses amount"""
        for property in self:
            property.total_expenses = sum(exp.amount for exp in property.expense_ids)

    @api.depends('payment_ids.amount', 'payment_ids.status', 'property_price','down_payment')
    def _compute_payment_remaining(self):
        """Calculate payments remaining amounts"""
        for property in self:
            installment_paid = sum(p.amount for p in property.payment_ids if p.status == 'paid')
            property.remaining_amount = property.property_price - installment_paid - property.down_payment

    @api.depends('property_price', 'total_expenses', 'investment_expenses')
    def _compute_total_cost(self):
        """ Calculate total cost for property"""
        total_cost = 0
        for property in self:
            total_cost = property.total_expenses
            if property.is_purchased:
                total_cost += property.property_price
            else:
                total_cost += property.investment_expenses
            property.total_cost = total_cost

    @api.depends('total_cost', 'property_price', 'management_fee_percentage')
    def _compute_financials(self):
        for property in self:
            if not property.is_purchased:
                property.total_profit = property.property_price - property.total_cost
                property.management_fee_amount = (property.total_profit * property.management_fee_percentage) / 100
                property.net_profit = property.total_profit - property.management_fee_amount
            else:
                property.total_profit = 0
                property.management_fee_amount = 0
                property.net_profit = 0

    # =========================== Constraints Functions ===========================

    @api.constrains('status')
    def _check_contact_when_confirmed_sale(self):
        for property in self:
            if property.status == 'draft': continue
            if not property.contact_id:
                raise ValidationError(_('Confirmed property must have a contact.'))

    @api.constrains('total_area', 'investment_id')
    def _check_area_for_sold_property(self):
        for property in self:
            if property.is_purchased:
                continue
            sold_area = property.get_sum_all_sold_properties_area()
            if property.investment_id.total_area < sold_area + property.total_area:
                raise ValidationError(_('All sold total area is greater than total area of investment.'))
        
    @api.constrains('total_area','property_price', 'down_payment','status')
    def _check_area_price_payment(self):
        for property in self:
            if property.total_area <= 0:
                raise ValidationError(_('Property area must be greater than zero.'))

            # Check property price
            if property.property_price == 0 and property.status == 'confirmed':
                raise ValidationError(_('Property price must be greater than zero.'))
            if property.property_price < 0:
                raise ValidationError(_('Property price must be positive.'))

            # Check property down_payment
            if property.down_payment < 0:
                raise ValidationError(_('Down payment cannot be negative.'))
            if property.down_payment > property.property_price:
                raise ValidationError(_('Down payment cannot exceed property price.'))

    @api.constrains('property_date', 'status')
    def _check_property_date(self):
        """Ensure purchase date is not later than related transaction dates"""
        for property in self:
            if property.status == 'draft': continue

            if not property.property_date:
                raise ValidationError(_('Confirmed property must have a date.'))
            
            if property.property_date > fields.Date.today():
                raise ValidationError(_('Property date cannot be in the future.'))

            # Check investment date
            if property.property_date < property.investment_id.open_date:
                raise ValidationError(
                    _('Cannot change property date to %s because investment %s with open date %s is Later.') % 
                    (property.property_date, property.investment_id.name, property.investment_id.open_date))
        
            # Check expenses (only partnership expenses) whith property date
            for expense in property.expense_ids:
                if expense.property_id.is_purchased:
                    if expense.expense_date < property.property_date:
                        raise ValidationError(
                            _('Cannot change purchased property date to %s because expense "%s" has date %s which is earlier. '
                            'Please update expense dates first or change property date.') % 
                            (property.property_date, expense.name, expense.expense_date))
                else:
                    if expense.expense_date > property.property_date:
                        raise ValidationError(
                            _('Cannot change sold property date to %s because expense "%s" has date %s which is later. '
                            'Please update expense dates first or change property date.') % 
                            (property.property_date, expense.name, expense.expense_date))
                    
            # Check property payment installments
            for payment in property.payment_ids:
                if payment.due_date < property.property_date:
                    raise ValidationError(
                        _('Cannot change property date to %s because payment "%s" has due date %s which is earlier. '
                          'Please update payment dates first.') % 
                        (property.property_date, payment.name, payment.due_date))

    # =========================== Action Functions ===========================

    def action_view_payments_Installments(self):
        """View payments installments for this property"""
        action = self.env.ref('real_estate_partnership_management_pro.action_purchase_payment_installment').read()[0]
        action['domain'] = [('property_id', '=', self.id)]
        action['context'] = {'default_property_id': self.id,}
        return action

    def action_view_expenses(self):
        """View property expenses"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Expenses'),
            'res_model': 'real.estate.expense',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id,'default_expense_type': 'investment',},
        }

    def action_view_property_profit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Profits'),
            'res_model': 'real.estate.sale.line',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
        }
    
    def action_create_expense(self):
        # Open expense creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Expense'),
            'res_model': 'real.estate.expense',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_expense_type': 'investment',
                'default_property_id': self.id,
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
                'default_property_id': self.id,
            },
        }

    def action_generate_purchase_payment_receipts(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Property Payment Receipts'),
            'res_model': 'property.payment.receipts.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
            },
        }

    def action_confirmed_sold_property(self):
        for property in self:
            if property.status == 'confirmed': continue
            restrict_sale_on_low_balance = self .env.company.restrict_sale_on_low_balance
            print("===================restrict_sale_on_low_balance", restrict_sale_on_low_balance)
            
            if property.investment_id.total_partnerships_percentage < 100:
                raise ValidationError(_('Cannot confirm property because investment total partnerships percentage is less than 100.'))

            property.investment_expenses = property.get_sold_property_investment_expense()

            vals_list = []
            for partnership in property.investment_id.partnership_ids:
                if restrict_sale_on_low_balance and partnership.remaining_amount > 0:
                    raise ValidationError(_('Cannot confirm property because partner "%s" has a remaining amount of partnership: %s. Please pay the pending amount before confirming the sale.') % (partnership.partner_id.name, partnership.name))

                partner_profit = (property.net_profit * partnership.percentage) / 100
                vals_list.append({
                    'property_id': self.id,
                    'partner_id': partnership.partner_id.id,
                    'profit_amount': partner_profit,
                })

            self.env['real.estate.sale.line'].create(vals_list)
            property.status = 'confirmed'


    def action_draft_sold_property(self):
        for property in self:
            if property.status == 'draft': continue

            property.sale_line_ids.unlink()

            property.investment_expenses = 0
            property.status = 'draft'

    # ============== Logic Functions  ========================
    def get_sum_all_sold_properties_area(self):
        sold_area = sum(sold.total_area for sold in self.investment_id.sold_properties_ids if sold.id != self.id)
        return sold_area

    def get_sum_confirmed_sold_properties_area(self):
            sold_area = sum(sold.total_area for sold in self.investment_id.sold_properties_ids if sold.id != self.id and sold.status == 'confirmed')
            return sold_area

    def get_remaining_expenses(self,investment_id):
        sold_investment_expenses = sum(sold.investment_expenses for sold in investment_id.sold_properties_ids)
        remaining_expenses = investment_id.total_cost_before_sold - sold_investment_expenses
        return remaining_expenses

    def get_sold_property_investment_expense(self):
        investment_id = self.investment_id
        property_area = self.total_area
        investment_area = investment_id.total_area

        # (1) Calculate total area of sold property
        sold_area = self.get_sum_confirmed_sold_properties_area()

        # (2) Apply the new formula
        remaining_area = investment_area - sold_area
        if remaining_area > 0:
            # Calculate expense ratio based on remaining area
            expense_ratio = (property_area / remaining_area) * 100
            # Calculate investment expenses from remaining expenses + parent profit from exits
            remaining_expenses = self.get_remaining_expenses(investment_id)
            investment_expenses = remaining_expenses * (expense_ratio / 100)
            return investment_expenses # Make it as (int) because I do not want any digits
        else:
            return 0.0