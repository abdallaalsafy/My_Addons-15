# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint

class RealEstateProperty(models.Model):
    _name = 'real.estate.property'
    _description = 'Real Estate Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'purchase_date desc'


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


    name = fields.Char(string='Property Name', required=True, tracking=True, index=True)
    code = fields.Char(string='Property Code', required=True, copy=False, default=lambda self: _('New'), index=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    
    # Property Type and Classification
    property_type = fields.Selection([
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('shop', 'Shop'),
        ('land', 'Land'),
        ('building', 'Building'),
        ('villa', 'Villa'),
        ('office', 'Office'),
        ('warehouse', 'Warehouse'),
    ], string='Property Type', required=True, tracking=True, index=True)
    
    # Location Information
    city_id = fields.Many2one('real.estate.city', string='City', tracking=True, index=True)
    state_id = fields.Many2one('real.estate.state', string='State/Province', tracking=True, index=True)
    address = fields.Text(string='Full Address', tracking=True)
    
    # Property Boundaries
    north_boundary = fields.Text(string='North Boundary', help='What borders the property from the north')
    south_boundary = fields.Text(string='South Boundary', help='What borders the property from the south')
    east_boundary = fields.Text(string='East Boundary', help='What borders the property from the east')
    west_boundary = fields.Text(string='West Boundary', help='What borders the property from the west')
    # Room Details
    built_area = fields.Float(string='Built Area', tracking=True)
    number_of_floors = fields.Integer(string='Number of Floors', tracking=True)
    total_rooms = fields.Integer(string='Total Rooms', tracking=True)
    bedrooms = fields.Integer(string='Bedrooms', tracking=True)
    bathrooms = fields.Integer(string='Bathrooms', tracking=True)
    kitchens = fields.Integer(string='Kitchens', tracking=True)
    living_rooms = fields.Integer(string='Living Rooms', tracking=True)

    # Property Specifications
    total_area = fields.Float(string='Total Area', required=True, compute='_compute_total_area', store=True, tracking=True,readonly=False,recursive=True)
    manual_total_area = fields.Float(string='Manual Total Area', tracking=True,required=True,
                                     help='Manual entry for total area (used when property is not a child with unit measurement)')
    sale_units = fields.Float(string='Sale Units', required=True,tracking=True,default=1,)
    total_units = fields.Integer(string='Total Units', tracking=True, default=1,required=True,
                                 help='Total number of units when sale method is by unit')
    area_unit = fields.Selection([
        ('meter', 'Square Meter (m²)'),
        ('qirat', 'Qirat'),
        ('unit', 'By Unit'),
    ], string='Area Unit', required=True, default='meter', tracking=True,help='Method used for calculating property sale and child creation')
    parent_area_unit = fields.Selection([
        ('meter', 'Square Meter (m²)'),
        ('qirat', 'Qirat'),
        ('unit', 'By Unit'),
    ], string='Parent Area Unit', compute='_compute_parent_area_unit', store=True, readonly=True,
                                 help='Area unit of the parent property (displayed for child properties only)')
    # Purchase Information
    seller_id = fields.Many2one('real.estate.contact', string='Purchased From', tracking=True, index=True)
    purchase_date = fields.Date(string='Purchase Date', required=True, tracking=True, index=True)
    purchase_price = fields.Float(string='Purchase Price', tracking=True, compute='_compute_child_purchase_price',
                                  recursive=True, store=True, readonly=False)
    down_payment = fields.Float(string='Down Payment', tracking=True, help='Down payment amount for the property purchase')
    remaining_purchase_amount = fields.Float(string='Remaining Purchase Amount', compute='_compute_payment_totals',
                                             store=True)
    purchase_payment_count = fields.Integer(string='Purchase Payment Count', compute='_compute_payment_counts')
    # investment Information
    investment_count = fields.Integer(string='Investment Count', compute='_compute_investment_count')
    total_investments = fields.Float(string='Total Investments', compute='_compute_investments', store=True)
    investment_method = fields.Selection([
        ('percentage', 'Percentage'),
        ('amount', 'Amount'),
    ], string='Investment Method', default='percentage', tracking=True,
       help='Determines how investments are recorded for this property')

    # Expenses Information
    total_expenses = fields.Float(string='Total Expenses', compute='_compute_expenses', store=True)
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
    # Expense Allocation for Child Properties
    expense_ratio = fields.Float(string='Expense Ratio (%)', compute='_compute_expense_allocation', store=True,
                                 help='Percentage of parent expenses allocated to this child property')
    allocated_expenses = fields.Float(string='Allocated Expenses', compute='_compute_expense_allocation', store=True,
                                      help='Amount of parent expenses allocated to this child property')
    total_children_expenses = fields.Float(string='Total Children Expenses', compute='_compute_children_expenses',
                                           store=True)
    # Financial Information
    current_value = fields.Float(string='Current Estimated Value', tracking=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)
    total_profit_from_exits = fields.Float(string='Total Profit from Partner Exits', 
                                          compute='_compute_total_profit_from_exits', store=True)

    status = fields.Selection([
        ('available', 'Available'),
        ('sold', 'Sold'),
    ], string='Status', default='available', tracking=True, index=True)
    # Sale Information
    sale_id = fields.Many2one('real.estate.property.sale', string='Sale', readonly=True, ondelete='cascade')
    sale_date = fields.Date(related='sale_id.sale_date', string='Sale Date', store=True, tracking=True,readonly=True)
    sale_price = fields.Float(related='sale_id.sale_price', string='Sale Price', store=True, tracking=True,readonly=True)
    sold_to_contact_id = fields.Many2one('real.estate.contact',related='sale_id.buyer_contact_id', store=True, string='Sold To', tracking=True,ondelete='restrict',readonly=True,)
    remaining_sale_amount = fields.Float(related='sale_id.remaining_balance', string='Remaining Sale Amount', store=True)
    sale_payment_count = fields.Integer(string='Sale Payment Count', compute='_compute_payment_counts')
    # Notes and Documents
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', help='Upload property documents, images, contracts, etc.')
    attachment_count = fields.Integer(string='Document Count', compute='_compute_attachment_count')

    # Parent/Child Relationship
    parent_id = fields.Many2one('real.estate.property', string='Parent Property', readonly=True, tracking=True, ondelete='cascade')
    is_child = fields.Boolean(string='Is Child Property', compute='_compute_is_child', store=True)
    has_any_children = fields.Boolean(string='All Children', compute='_compute_has_children', store=True)
    child_count = fields.Integer(string='Child Count', compute='_compute_child_count')
    
    # Related Data
    child_ids = fields.One2many('real.estate.property', 'parent_id', string='Child Properties')
    investment_ids = fields.One2many('real.estate.property.investment', 'property_id', string='Investments')
    expense_ids = fields.One2many('real.estate.expense', 'property_id', string='Expenses')
    sale_line_ids = fields.One2many('real.estate.property.sale.line', 'property_id', string='Sale Lines')
    exit_ids = fields.One2many('real.estate.partner.exit', 'property_id', string='Exitings')
    purchase_payment_ids = fields.One2many('real.estate.payment.installment', 'property_id', string='Purchase Payments',
                                          domain=[('payment_type', '=', 'purchase')])
    sale_payment_ids = fields.One2many('real.estate.payment.installment', 'property_id', string='Sale Payments',
                                       domain=[('payment_type', '=', 'sale')])

    # ====================== Built-in methods =================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.property') or _('New')

        properties = super(RealEstateProperty, self).create(vals_list)
        
        # Create down payment installment if down_payment is specified (only for parent properties)
        for property in properties:
            if property.down_payment > 0 and not property.is_child:
                property._create_down_payment_installment()
        
        return properties

    def write(self, vals):
        property_affecting_fields = ['total_area', 'area_unit', 'purchase_price', 'total_units', 'parent_area_unit',
                                     'parent_total_units', 'manual_total_area']
        if any(field in vals for field in property_affecting_fields):
            for property in self:
                if property.status == 'sold':
                    raise ValidationError(
                        _('Cannot update sold property "%s"') % (
                                property.name or property.code)
                    )
                # If it's a parent with sold child properties, don't allow deletion
                if property.child_ids and property.child_ids.filtered(lambda c: c.status == 'sold'):
                    raise ValidationError(
                        _('Cannot delete property with sold child properties.'))

        """Override write to add automatic parent status change when all children are sold"""
        result = super(RealEstateProperty, self).write(vals)
        if 'status' in vals and vals['status'] == 'sold':
            self._mark_sold_parent_property_which_has_children()

        # Handle down payment installment updates (only for parent properties)
        if 'down_payment' in vals:
            for property in self:
                if not property.is_child:
                    if property.down_payment > 0:
                        property._update_down_payment_installment()
                    else:
                        property._delete_down_payment_installment()

        return result

    def unlink(self):
        """Override unlink to add validation before deletion"""
        for property in self:
            # Check if property is sold
            if property.status == 'sold':
                raise ValidationError(_('Cannot delete sold property.'))

            # If it's a parent with sold child properties, don't allow deletion
            if property.child_ids and property.child_ids.filtered(lambda c: c.status == 'sold'):
                raise ValidationError(
                    _('Cannot delete property with sold child properties.'))

            # Check if property has investments
            if property.investment_ids and property.investment_ids.filtered(lambda c: c.status != 'confirmed'):
                raise ValidationError(_('Cannot delete property with distributed or Withdrawn investments.'))

            # Check if property has exiting
            if property.exit_ids:
                raise ValidationError(_('Cannot delete property with exiting.'))

            # Because Partner need investment_ids in compute Field
            # Because this line compute field cannot be computedS
            property.investment_ids.unlink()
        return super(RealEstateProperty, self).unlink()

    # =========================== Onchange Functions ===========================

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        """Set area unit based on parent and make readonly when parent is unit"""
        if self.parent_id:
            # Child inherits parent's area unit
            self.area_unit = self.parent_id.area_unit

    # =========================== Compute Functions ===========================

    def _compute_attachment_count(self):
        for property in self:
            property.attachment_count = len(property.attachment_ids)

    def _compute_child_count(self):
        for property in self:
            property.child_count = len(property.child_ids)

    def _compute_investment_count(self):
        for property in self:
            property.investment_count = len(property.investment_ids)

    def _compute_expense_count(self):
        for property in self:
            property.expense_count = len(property.expense_ids)

    def _compute_payment_counts(self):
        """Calculate payment counts"""
        for property in self:
            property.purchase_payment_count = len(property.purchase_payment_ids)
            property.sale_payment_count = len(property.sale_payment_ids)

    @api.depends('parent_id')
    def _compute_is_child(self):
        for property in self:
            property.is_child = bool(property.parent_id)

    @api.depends('child_ids')
    def _compute_has_children(self):
        for property in self:
            property.has_any_children = bool(property.child_ids)

    @api.depends('parent_id.area_unit')
    def _compute_parent_area_unit(self):
        for property in self:
            property.parent_area_unit = property.parent_id.area_unit if property.parent_id else False

    @api.depends('manual_total_area', 'parent_id.total_area', 'parent_id.total_units', 'sale_units', 'area_unit', 'is_child')
    def _compute_total_area(self):
        for property in self:
            if property.is_child and property.area_unit == 'unit':
                # Calculate: (parent_total_area / parent_total_units) * sale_units
                if property.parent_id.total_units > 0:
                    property.total_area = (property.parent_id.total_area / property.parent_id.total_units) * property.sale_units
                else:
                    property.total_area = 0.0
            else:
                # Use manual total area for other cases
                property.total_area = property.manual_total_area

    #====================== Compute Calc Fields ===========================

    @api.depends('child_ids.total_expenses', 'child_ids')
    def _compute_children_expenses(self):
        """ Calculate total expenses of activ child properties"""
        for property in self:
            if property.child_ids:
                property.total_children_expenses = sum(
                    child.total_expenses
                    for child in property.child_ids
                )
            else:
                property.total_children_expenses = 0.0

    @api.depends('investment_ids','investment_ids.amount', 'investment_ids.status')
    def _compute_investments(self):
        """Calculate total confirmed or distributed investments amount"""
        for property in self:
            property.total_investments = sum(
                inv.amount for inv in property.investment_ids if inv.status in ['confirmed', 'distributed'])

    @api.depends('expense_ids','expense_ids.amount')
    def _compute_expenses(self):
        """ Calculate total confirmed or paid expenses amount"""
        for property in self:
            property.total_expenses = sum(exp.amount for exp in property.expense_ids)

    @api.depends('purchase_payment_ids','purchase_payment_ids.amount', 'purchase_payment_ids.status', 'purchase_price')
    def _compute_payment_totals(self):
        """Calculate payment totals and remaining amounts"""
        for property in self:
            # Purchase payments (only count paid installments)
            purchase_paid = sum(p.amount for p in property.purchase_payment_ids if p.status == 'paid')
            property.remaining_purchase_amount = property.purchase_price - purchase_paid

    @api.depends('exit_ids.actual_property_profit')
    def _compute_total_profit_from_exits(self):
        """Calculate total profit from approved partner exit lines for this property"""
        for property in self:
            property.total_profit_from_exits = sum(exit.actual_property_profit for exit in property.exit_ids)

    @api.depends('parent_id', 'parent_id.purchase_price', 'parent_id.area_unit', 'parent_id.total_area', 'total_area', 'area_unit')
    def _compute_child_purchase_price(self):
        """Auto-calculate purchase price for child properties based on area ratio"""
        for property in self:
            if property.parent_id:
                property.purchase_price = self._get_child_purchase_price_by_area_ratio(property.parent_id,
                                                                                       property.total_area,
                                                                                       property.area_unit)
            else:
                # For parent properties, keep manual purchase price
                pass

    @api.depends('parent_id', 'parent_id.total_expenses', 'parent_id.total_area', 'parent_id.area_unit','parent_id.total_profit_from_exits', 'total_area', 'area_unit')
    def _compute_expense_allocation(self):
        """ calculate expense allocation for child properties based on area ratio"""
        for property in self:
            if property.parent_id:
                if property.status == 'sold':
                    continue
                property.expense_ratio, property.allocated_expenses = property.get_child_expense_allocation_by_area_ratio()
            else:
                property.expense_ratio = 0.0
                property.allocated_expenses = 0.0

    @api.depends('purchase_price', 'total_expenses', 'allocated_expenses', 'total_profit_from_exits','total_children_expenses')
    def _compute_total_cost(self):
        """ Calculate total cost for property"""
        for property in self:
            # For parent properties, use own expenses
            property.total_cost = property.purchase_price + property.total_expenses

            if property.is_child:
                # For child properties, use allocated expenses from parent
                property.total_cost += property.allocated_expenses
            else:
                # For parent properties, add profit from exits
                property.total_cost += property.total_profit_from_exits + property.total_children_expenses

    # =========================== Constraints Functions ===========================
    @api.constrains('is_child')
    def _check_is_child(self):
        for property in self:
            if property.is_child and property.parent_id.parent_id:
                raise ValidationError(_('Cannot create child property from another child property.'))

    @api.constrains('seller_id')
    def _check_seller_deletion(self):
        for property in self:
            if (property.purchase_payment_ids or property.down_payment > 0) and not property.seller_id:
                raise ValidationError(
                    _('Seller must be specified when down payment is set or remaining purchase amount is set.'))

    @api.constrains('area_unit')
    def _check_area_unit_change(self):
        """Validate area unit changes between parent and child properties"""
        for property in self:
            # Rule 1: If parent has unit measurement and has children, cannot change parent's unit
            if not property.is_child and property.area_unit == 'unit' and property.child_ids:
                all_equl_unit = all(child.area_unit == 'unit' for child in property.child_ids)
                if not all_equl_unit:
                    raise ValidationError(
                        _('Cannot change area unit of parent property to "By Unit" when it has child properties.'))

            # Rule 3: Child cannot change to unit if parent is not unit
            if property.is_child and property.area_unit == 'unit' and property.parent_id.area_unit != 'unit':
                raise ValidationError(
                    _('Cannot change child property area unit to "By Unit" when parent property unit is not "By Unit".'))

            # Rule 4: Child cannot change from unit if parent is unit
            if property.is_child and property.area_unit != 'unit' and property.parent_id.area_unit == 'unit':
                raise ValidationError(
                    _('Cannot change child property area unit from "By Unit" when parent property unit is "By Unit".'))

    @api.constrains('built_area','total_area','number_of_floors','purchase_price', 'down_payment')
    def _check_areas(self):
        for property in self:
            if property.total_area <= 0:
                raise ValidationError(_('Property area must be greater than zero.'))
            if property.built_area and property.built_area > property.total_area:
                raise ValidationError(_('Built area cannot be greater than total area.'))
            if property.number_of_floors < 0:
                raise ValidationError(_('Number of floors cannot be negative.'))

            # Check purchase price of the property
            if property.purchase_price <= 0:
                raise ValidationError(_('Purchase price must be positive.'))
            # Down payment validations only for parent properties
            if not property.is_child:
                if property.down_payment < 0:
                    raise ValidationError(_('Down payment cannot be negative.'))
                if property.down_payment > property.purchase_price:
                    raise ValidationError(_('Down payment cannot exceed purchase price.'))


    @api.constrains('purchase_price','total_area', 'area_unit', 'parent_id')
    def _check_no_change_main_fields_for_sold_property(self):
        """Prevent changing parent purchase price when there are sold child properties"""
        for property in self:
            # Only check for parent properties (not children)
            if property.status == 'sold':
                raise ValidationError(
                    _('Cannot change purchase price,area unit or total area of sold property "%s"') % (property.name or property.code)
                )
            if property.has_any_children:
                # Check if there are any sold child properties
                sold_children = property.child_ids.filtered(lambda child: child.status == 'sold')
                if sold_children:
                    raise ValidationError(
                                _('Cannot change purchase price of parent property "%s" while there are sold child properties. '
                                  'Sold children: %s') %
                                (property.name or property.code,
                                 ', '.join(child.name or child.code for child in sold_children))
                            )

    @api.constrains('investment_method')
    def _check_investment_method_change(self):
        """Prevent changing investment method when investments exist"""
        for property in self:
            if property.is_child:
                continue
            if property.investment_count > 0:
                raise ValidationError(
                    _('Cannot change investment method for property "%s" while there are existing investments. '
                      'Please remove all investments before changing the investment method.') %
                    (property.name or property.code)
                )

    @api.constrains('total_area', 'area_unit', 'parent_id')
    def validate_children_area_within_parent(self):
        """Validate that total children area doesn't exceed parent area"""
        for property in self:
            parent_property = property.parent_id if property.is_child else property
            parent_area_meters = self._convert_to_meters(parent_property.total_area, parent_property.area_unit)

            # Get total children area using the new function
            current_children_area = self._get_children_total_area(parent_property)

            # Check if children area would exceed parent area
            if current_children_area > parent_area_meters + 0.01:  # Allow small floating point differences
                raise ValidationError(
                    _('Total area of all child properties (%.2f m²) cannot exceed parent property area (%.2f m²). '
                      'Current excess would be: %.2f m²') %
                    (current_children_area, parent_area_meters,
                     current_children_area - parent_area_meters)
                )

    @api.constrains('purchase_date')
    def _check_purchase_date_consistency(self):
        """Ensure purchase date is not later than related transaction dates"""
        for property in self:
            if not property.purchase_date:
                return
            
            # Check investments
            for investment in property.investment_ids:
                if investment.investment_date < property.purchase_date:
                    raise ValidationError(
                        _('Cannot change purchase date to %s because investment "%s" has date %s which is earlier. '
                          'Please update investment dates first.') % 
                        (property.purchase_date, investment.name, investment.investment_date))
            
            # Check expenses (only investment expenses)
            for expense in property.expense_ids.filtered(lambda e: e.expense_type == 'investment'):
                if expense.expense_date < property.purchase_date:
                    raise ValidationError(
                        _('Cannot change purchase date to %s because expense "%s" has date %s which is earlier. '
                          'Please update expense dates first.') % 
                        (property.purchase_date, expense.name, expense.expense_date))
            
            # Check sale
            if property.sale_id and property.sale_id.sale_date < property.purchase_date:
                raise ValidationError(
                    _('Cannot change purchase date to %s because sale "%s" has date %s which is earlier. '
                      'Please update sale date first.') % 
                    (property.purchase_date, property.sale_id.name, property.sale_id.sale_date))
            
            # Check partner exits
            for exit in property.exit_ids:
                if exit.exit_date < property.purchase_date:
                    raise ValidationError(
                        _('Cannot change purchase date to %s because partner exit "%s" has date %s which is earlier. '
                          'Please update exit dates first.') % 
                        (property.purchase_date, exit.name, exit.exit_date))
            
            # Check purchase payment installments
            for payment in property.purchase_payment_ids:
                if payment.due_date < property.purchase_date:
                    raise ValidationError(
                        _('Cannot change purchase date to %s because payment "%s" has due date %s which is earlier. '
                          'Please update payment dates first.') % 
                        (property.purchase_date, payment.name, payment.due_date))

    # ====================== validation functions ===========================
    def validate_confirmed_investment_percentage_and_total_amount(self):
        """Validate that total investment percentage is 100%"""
        parent_property = self.parent_id if self.parent_id else self
        confirmed_investments = parent_property.investment_ids.filtered(lambda inv: inv.status == 'confirmed')
        if confirmed_investments:
            total_percentage = sum(inv.percentage for inv in confirmed_investments)
            if not (99.99 <= total_percentage <= 100.01):  # Allow small floating point differences
                raise ValidationError(
                    _('Cannot mark property as sold: Total investment percentage must be 100%%. Current total: %.2f%%') % total_percentage)

            total_investments = sum(inv.amount for inv in confirmed_investments)
            if not total_investments > 0:
                raise ValidationError(_('Cannot confirm sale: No total investments found for this property.'))

        else:
            raise ValidationError(_('Cannot mark property as sold: No confirmed investments found.'))

    # =========================== Action Functions ===========================
    def action_view_purchase_payments(self):
        """View purchase payments for this property"""
        self.ensure_one()
        action = self.env.ref('real_estate_partnership_management.action_purchase_payment_installment').read()[0]
        action['domain'] = [('property_id', '=', self.id),('payment_type','=', 'purchase')]
        action['context'] = {'default_property_id': self.id, 'default_payment_type': 'purchase'}
        return action

    def action_view_sale_payments(self):
        """View sale payments for this property"""
        self.ensure_one()
        action = self.env.ref('real_estate_partnership_management.action_sale_payment_installment').read()[0]
        action['domain'] = [('property_id', '=', self.id),('payment_type','=', 'sale')]
        action['context'] = {'default_property_id': self.id, 'default_payment_type': 'sale'}
        return action

    def action_view_investments(self):
        """View property investments"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Investments'),
            'res_model': 'real.estate.property.investment',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id,'readonly_property_id': True,},
        }

    def action_add_investment(self):
        """Add new investment for property with validation"""
        self.ensure_one()
        
        # Validate property can accept new investment
        self.env['real.estate.property.investment'].validate_property_for_investment(self)
        
        # Open investment creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Investment'),
            'res_model': 'real.estate.property.investment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
                'readonly_property_id': True,
            },
        }

    def action_add_expense(self):
        """Add new expense for property with validation"""
        self.ensure_one()
        
        # Validate property can accept new expense
        self.env['real.estate.expense'].validate_property_for_expense(self)
        
        # Open expense creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Expense'),
            'res_model': 'real.estate.expense',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
                'default_expense_type': 'investment',
                'readonly_property_id': True,
            },
        }

    def action_open_partner_exit(self):
        """Open the Partner Exit form prefilled for this property."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Exit Request'),
            'res_model': 'real.estate.partner.exit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
            }
        }

    def action_view_expenses(self):
        """View property expenses"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Expenses'),
            'res_model': 'real.estate.expense',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id,'readonly_property_id': True,},
        }

    def action_view_children(self):
        """View child properties"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Child Properties'),
            'res_model': 'real.estate.property',
            'view_mode': 'tree,form',
            'domain': [('parent_id', '=', self.id)],
            'context': {'default_parent_id': self.id},
        }

    def action_add_purchase_payment(self):
        """Add new purchase payment for property with validation"""
        self.ensure_one()
        
        # Validate property can accept new purchase payment
        self.env['real.estate.payment.installment'].validate_property_for_purchase_payment(self)
        
        # Open purchase payment creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Purchase Payment'),
            'res_model': 'real.estate.payment.installment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
                'default_payment_type': 'purchase',
                'default_contact_id': self.seller_id.id if self.seller_id else False,
                'readonly_property_id': True,
            },
        }

    def action_generate_purchase_payment_receipts(self):
        """Open wizard to generate multiple purchase payment receipts"""
        self.ensure_one()
        
        # Validate property can accept new purchase payment
        self.env['real.estate.payment.installment'].validate_property_for_purchase_payment(self)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Purchase Payment Receipts'),
            'res_model': 'purchase.payment.receipts.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
            },
        }

    def action_add_sale_payment(self):
        """Add new sale payment for property with validation"""
        self.ensure_one()
        
        # Validate property can accept new sale payment
        self.env['real.estate.payment.installment'].validate_property_for_sale_payment(self)
        
        # Open sale payment creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Sale Payment'),
            'res_model': 'real.estate.payment.installment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
                'default_payment_type': 'sale',
                'default_contact_id': self.sold_to_contact_id.id if self.sold_to_contact_id else False,
                'readonly_property_id': True,
            },
        }

    def action_create_child_property(self):
        """Create child property for partial sale"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Child Property'),
            'res_model': 'real.estate.property',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_id': self.id,
                'default_name': _('%s - Child Property %s') % (self.code, len(self.child_ids) + 1),
                'default_property_type': self.property_type,
                'default_city_id': self.city_id.id,
                'default_state_id': self.state_id.id,
                'default_address': self.address,
                'default_status': 'available',
                'default_purchase_date': fields.Date.today(),
                'default_area_unit': self.area_unit,
            },
        }

    def action_sell_property(self):
        """Open property sale form with default data"""
        if self.status != 'available':
            raise ValidationError(_('Property must be available to sell it.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Property Sale'),
            'res_model': 'real.estate.property.sale',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
                'default_sale_date': fields.Date.today(),
                'default_sale_price': self.current_value,
                'readonly_property_id': True,
            },
        }

    # ============== Logic Functions  ========================
    def get_child_expense_allocation_by_area_ratio(self):
        """
        Calculate expense allocation for a child property based on area ratio
        Returns:
            tuple: (expense_ratio, allocated_expenses)
        """
        parent_id = self.parent_id
        total_area = self.total_area
        area_unit = self.area_unit
        if not parent_id or not total_area or not parent_id.total_area:
            return 0.0, 0.0

        # Convert areas to meters for accurate calculation
        child_area_meters = self._convert_to_meters(total_area, area_unit)
        parent_area_meters = self._convert_to_meters(parent_id.total_area, parent_id.area_unit)

        # Calculate total area of sold children
        sold_children_area = 0
        for child in parent_id.child_ids:
            if child.status == 'sold':
                sold_children_area += self._convert_to_meters(child.total_area, child.area_unit)

        # Calculate total allocated expenses of sold children
        sold_children_expenses = sum(
            child.allocated_expenses for child in parent_id.child_ids
            if child.status == 'sold'
        )

        # Apply the new formula
        remaining_area = parent_area_meters - sold_children_area
        if remaining_area > 0:
            # Calculate expense ratio based on remaining area
            expense_ratio = (child_area_meters / remaining_area) * 100
            # Calculate allocated expenses from remaining expenses + parent profit from exits
            remaining_expenses = (parent_id.total_expenses + parent_id.total_profit_from_exits) - sold_children_expenses
            allocated_expenses = remaining_expenses * (expense_ratio / 100)
            return expense_ratio, allocated_expenses
        else:
            return 0.0, 0.0

    def _mark_sold_parent_property_which_has_children(self):
        """Mark parent property as sold manually"""
        for Property in self:
            if not(Property.status == 'sold' and Property.parent_id and Property.parent_id.status != 'sold'):
                continue

            parent_property = Property.parent_id

            # Convert parent area to meters using helper function
            parent_area_meters = self._convert_to_meters(parent_property.total_area, parent_property.area_unit)

            # Calculate total area of all children
            total_children_area = self._get_children_total_area(parent_property)

            # 2: Check if there are any unsold child properties
            unsold_children = parent_property.child_ids.filtered(lambda child: child.status != 'sold')
            if unsold_children:
                continue
            # 3: Validate area match between parent and children
            # Allow small floating point differences (0.01 tolerance)
            if abs(total_children_area - parent_area_meters) > 0.01:
                continue

            parent_property.write({
                'status': 'sold',
                'sale_date': fields.Date.today(),
                'sale_price': sum(child.sale_price for child in self.child_ids)
            })

            # Distribute investments when parent is sold
            parent_property._distribute_investments_on_sale()

    def _distribute_investments_on_sale(self):
        """Change confirmed investments to distributed status when property is sold"""
        confirmed_investments = self.investment_ids.filtered(lambda inv: inv.status == 'confirmed')
        confirmed_investments.write({'status': 'distributed'})

    def _get_child_purchase_price_by_area_ratio(self,parent_id,total_area, area_unit):
        """
        Calculate purchase price for a child property based on area ratio
        Returns:
            float: Calculated purchase price based on area ratio
        """
        # Convert both areas to meters using helper function
        child_area_meters = self._convert_to_meters(total_area, area_unit)
        parent_area_meters = self._convert_to_meters(parent_id.total_area, parent_id.area_unit)

        if parent_area_meters > 0:
            area_ratio = child_area_meters / parent_area_meters
            return parent_id.purchase_price * area_ratio

        return 0.0

    def _get_children_total_area(self,parent_property,status='all'):#status= 'all' or 'sold' or 'active'
        # Calculate total area of all sold children
        total_children_area = 0
        if status == 'all':
            childrens = parent_property.child_ids
        elif status == 'sold':
            childrens = parent_property.child_ids.filtered(lambda child: child.status == 'sold')
        else:
            childrens = parent_property.child_ids.filtered(lambda child: child.status != 'sold')

        for child in childrens:
            total_children_area += self._convert_to_meters(child.total_area, child.area_unit)

        return total_children_area

    def _create_down_payment_installment(self):
        """Create a down payment installment for this property"""
        if not self.seller_id:
            return
        
        installment_vals = {
            'property_id': self.id,
            'contact_id': self.seller_id.id,
            'payment_type': 'purchase',
            'amount': self.down_payment,
            'due_date': self.purchase_date,
            'status': 'paid',
            'is_down_payment': True,
            'payment_method': 'cash',  # Default payment method
            'payment_reference': f'Down payment for property {self.code}',
        }
        
        self.env['real.estate.payment.installment'].create(installment_vals)

    def _update_down_payment_installment(self):
        """Update the down payment installment amount"""
        down_payment_installment = self.purchase_payment_ids.filtered(lambda p: p.is_down_payment)
        if down_payment_installment:
            down_payment_installment[0].write({'amount': self.down_payment})
        else:
            # If no down payment installment exists, create one
            self._create_down_payment_installment()

    def _delete_down_payment_installment(self):
        """Delete the down payment installment"""
        down_payment_installment = self.purchase_payment_ids.filtered(lambda p: p.is_down_payment)
        if down_payment_installment:
            down_payment_installment.unlink()