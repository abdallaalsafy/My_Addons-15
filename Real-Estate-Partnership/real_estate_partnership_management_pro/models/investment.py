# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint
from .property import RealEstateProperty as property

class RealEstateInvestment(models.Model):
    _name = 'real.estate.investment'
    _description = 'Real Estate Investment'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Name', required=True, tracking=True, index=True)
    code = fields.Char(string='Code', required=True, copy=False, default=lambda self: _('New'), index=True)
    open_date = fields.Date(string='Open Date', required=True, default=fields.Date.today, tracking=True)
    close_date = fields.Date(string='Close Date', readonly=True, tracking=True)
    is_restructured = fields.Boolean(string='Restructured', default=False, tracking=True)
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    
    investment_method = fields.Selection([
            ('percentage', 'Percentage'),
            ('amount', 'Amount'),
        ], string='Investment Method', default='percentage', tracking=True,
           help='Determines how partnerships are recorded for this investment. If set to "Percentage", partnerships will be recorded as a percentage of the total investment. If set to "Amount", partnerships will be recorded as a fixed amount.')
    status = fields.Selection([
                ('opening', 'Opening'),
                ('closed', 'Closed'),
            ], string='Status', default='opening', tracking=True, index=True)
    
    investment_type = fields.Selection(property._SELECTION_PROPERTY_TYPE, string='Investment Type', required=True, index=True)
    area_unit = fields.Selection(property._SELECTION_AREA_UNIT, string='Area Unit', required=True, index=True, help='Unit of measurement for the property area')
    # Location Information
    city_id = fields.Many2one('real.estate.city', string='City', tracking=True, index=True)
    address = fields.Text(string='Full Address', tracking=True)
    # Property Boundaries
    north_boundary = fields.Text(string='North Boundary', compute='_compute_purchased_property_boundary', store=True, readonly=False, help='What borders the property from the north')
    south_boundary = fields.Text(string='South Boundary', compute='_compute_purchased_property_boundary', store=True, readonly=False, help='What borders the property from the south')
    east_boundary = fields.Text(string='East Boundary', compute='_compute_purchased_property_boundary', store=True, readonly=False, help='What borders the property from the east')
    west_boundary = fields.Text(string='West Boundary', compute='_compute_purchased_property_boundary', store=True, readonly=False, help='What borders the property from the west')
    # Room Details
    built_area = fields.Float(string='Built Area', tracking=True, compute='_compute_purchased_property_rooms', store=True, help='Built area of the property (used for area ratio calculations)')
    number_of_floors = fields.Integer(string='Number of Floors', tracking=True, compute='_compute_purchased_property_rooms', store=True, help='Number of floors in the property')
    total_rooms = fields.Integer(string='Total Rooms', tracking=True,  compute='_compute_purchased_property_rooms', store=True, help='Total number of rooms in the property')
    bedrooms = fields.Integer(string='Bedrooms', tracking=True, compute='_compute_purchased_property_rooms', store=True, help='Number of bedrooms in the property')
    bathrooms = fields.Integer(string='Bathrooms', tracking=True, compute='_compute_purchased_property_rooms', store=True, help='Number of bathrooms in the property')
    kitchens = fields.Integer(string='Kitchens', tracking=True, compute='_compute_purchased_property_rooms', store=True, help='Number of kitchens in the property')
    living_rooms = fields.Integer(string='Living Rooms', tracking=True, compute='_compute_purchased_property_rooms', store=True, help='Number of living rooms in the property')
    # Area and Units
    total_area = fields.Float(string='Total Area', compute='_compute_total_area', store=True,)
    sold_area = fields.Float(string='Sold Area', compute='_compute_sold_remaining_area', store=True,)
    remaining_area = fields.Float(string='Remaining Area', compute='_compute_sold_remaining_area', store=True,)
    # Financial Information
    total_current_value = fields.Monetary(string='Total Current Value', currency_field='company_currency', compute='_compute_total_current_value', store=True)
    total_investment_cost = fields.Monetary(string='Total Investment Cost', currency_field='company_currency', compute='_compute_total_investment_cost', store=True)
    total_cost_before_sold = fields.Monetary(string='Total Purchase Cost', currency_field='company_currency', compute='_compute_total_investment_cost', store=True)
    total_expenses = fields.Monetary(string='Total Expenses', currency_field='company_currency', compute='_compute_investment_expenses', store=True)
    total_partnerships = fields.Monetary(string='Total Partnerships', currency_field='company_currency', compute='_compute_partnerships', store=True)
    total_partnerships_percentage = fields.Float(string='Total Percentage', compute='_compute_total_partnerships_percentage', store=True)
    
    # Counts for related records
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
    partnership_count = fields.Integer(string='Partnership Count', compute='_compute_partnership_count')
    attachment_count = fields.Integer(string='Document Count', compute='_compute_attachment_count')
    purchased_properties_count = fields.Integer(string='Purchased Properties Count', compute='_compute_properties_count')
    sold_properties_count = fields.Integer(string='Sold Properties Count', compute='_compute_properties_count')
    confirmed_sold_properties_count = fields.Integer(string='ConfirmedSold Properties Count', compute='_compute_properties_count')
    draft_sold_properties_count = fields.Integer(string='Draft Sold Properties Count', compute='_compute_properties_count', store=True)
    profit_count = fields.Integer(string='Profit Count', compute='_compute_profit_count')
    
    # Notes and Documents
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', help='Upload property documents, images, properties, etc.')
    
    # Related Data
    purchased_properties_ids = fields.One2many('real.estate.property', 'investment_id', string='Purchased Properties', domain=[('is_purchased', '=', True)])
    sold_properties_ids = fields.One2many('real.estate.property', 'investment_id', string='Sold Properties', domain=[('is_purchased', '=', False)])
    partnership_ids = fields.One2many('real.estate.partnership', 'investment_id', string='Partnerships')
    expense_ids = fields.One2many('real.estate.expense', 'investment_id', string='Expenses')
    sale_line_ids = fields.One2many('real.estate.sale.line', 'investment_id', string='Sale Lines')

    # ====================== Built-in methods =================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.investment') or _('New')

        investments = super(RealEstateInvestment, self).create(vals_list)
        return investments

    def write(self, vals):
        result = super(RealEstateInvestment, self).write(vals)

        if 'investment_method' in vals:
            self.env['real.estate.partnership.payment'].get_percentage_value(self.partnership_ids)
        return result

    def unlink(self):
        for investment in self:
            if investment.status == 'closed':
                raise ValidationError(_('You cannot delete an closed investment'))
            # Because Partner need partnership_ids in compute Field
            # Because this line compute field cannot be computedS
            investment.partnership_ids.unlink()
        return super(RealEstateInvestment, self).unlink()

    # =========================== Compute Functions ===========================

    def _compute_properties_count(self):
        for investment in self:
            investment.purchased_properties_count = len(investment.purchased_properties_ids)
            investment.sold_properties_count = len(investment.sold_properties_ids)
            investment.confirmed_sold_properties_count = len([property for property in investment.sold_properties_ids if property.status == 'confirmed'])
            investment.draft_sold_properties_count = len([property for property in investment.sold_properties_ids if property.status == 'draft'])

    def _compute_expense_count(self):
        for investment in self:
            investment.expense_count = len(investment.expense_ids)

    def _compute_partnership_count(self):
            for investment in self:
                investment.partnership_count = len(investment.partnership_ids)

    def _compute_attachment_count(self):
        for investment in self:
            investment.attachment_count = len(investment.attachment_ids)

    def _compute_profit_count(self):
        for investment in self:
            investment.profit_count = len(investment.sale_line_ids)
    #-------------------------------------------------

    @api.depends('purchased_properties_ids.area_unit')
    def _compute_purchased_property_area_unit(self):
        for investment in self:
            if investment.purchased_properties_ids:
                # Assuming the first purchased property's area unit is representative
                first_property = investment.purchased_properties_ids[0]
                investment.area_unit = first_property.area_unit
            else:
                investment.area_unit = False

    @api.depends('purchased_properties_ids.built_area', 'purchased_properties_ids.number_of_floors', 'purchased_properties_ids.total_rooms', 'purchased_properties_ids.bedrooms', 'purchased_properties_ids.bathrooms', 'purchased_properties_ids.kitchens', 'purchased_properties_ids.living_rooms')
    def _compute_purchased_property_rooms(self):
        for investment in self:
            # If there are purchased properties, sum their room specifications; otherwise, set to zero
            if investment.purchased_properties_ids:
                investment.built_area = sum(property.built_area for property in investment.purchased_properties_ids)
                investment.number_of_floors = sum(property.number_of_floors for property in investment.purchased_properties_ids)
                investment.total_rooms = sum(property.total_rooms for property in investment.purchased_properties_ids)
                investment.bedrooms = sum(property.bedrooms for property in investment.purchased_properties_ids)
                investment.bathrooms = sum(property.bathrooms for property in investment.purchased_properties_ids)
                investment.kitchens = sum(property.kitchens for property in investment.purchased_properties_ids)
                investment.living_rooms = sum(property.living_rooms for property in investment.purchased_properties_ids)
            else:
                investment.built_area = 0
                investment.number_of_floors = 0
                investment.total_rooms = 0
                investment.bedrooms = 0
                investment.bathrooms = 0
                investment.kitchens = 0
                investment.living_rooms = 0

    @api.depends('purchased_properties_ids.north_boundary', 'purchased_properties_ids.south_boundary', 'purchased_properties_ids.east_boundary', 'purchased_properties_ids.west_boundary')
    def _compute_purchased_property_boundary(self):
        for investment in self:
            if len(investment.purchased_properties_ids) == 1:
                # Assuming the first purchased property's boundaries are representative
                first_property = investment.purchased_properties_ids[0]
                investment.north_boundary = first_property.north_boundary
                investment.south_boundary = first_property.south_boundary
                investment.east_boundary = first_property.east_boundary
                investment.west_boundary = first_property.west_boundary
            else:
                investment.north_boundary = False
                investment.south_boundary = False
                investment.east_boundary = False
                investment.west_boundary = False

    @api.depends('purchased_properties_ids.current_value')
    def _compute_total_current_value(self):
        for investment in self:
            if investment.purchased_properties_ids:
                investment.total_current_value = sum(property.current_value for property in investment.purchased_properties_ids)
            else:
                investment.total_current_value = 0.0

    @api.depends('purchased_properties_ids.total_cost', 'sold_properties_ids.total_expenses', 'total_expenses')
    def _compute_total_investment_cost(self):
        for investment in self:
            total_purchase_properties_cost = sum(property.total_cost for property in investment.purchased_properties_ids)
            total_sold_properties_expenses = sum(property.total_expenses for property in investment.sold_properties_ids)
            total_cost_before_sold = total_purchase_properties_cost + investment.total_expenses
            investment.total_investment_cost = total_cost_before_sold + total_sold_properties_expenses
            investment.total_cost_before_sold = total_cost_before_sold

    @api.depends('purchased_properties_ids.total_area')
    def _compute_total_area(self):
        for investment in self:
            if investment.purchased_properties_ids:
                investment.total_area = sum(property.total_area for property in investment.purchased_properties_ids)
            else:
                investment.total_area = 0.0

    @api.depends('sold_properties_ids.total_area', 'total_area')
    def _compute_sold_remaining_area(self):
        for investment in self:
            investment.sold_area = sum(property.total_area for property in investment.sold_properties_ids)
            investment.remaining_area = investment.total_area - investment.sold_area

    @api.depends('expense_ids.amount')
    def _compute_investment_expenses(self):
        """ Calculate total confirmed or paid expenses amount"""
        for investment in self:
            investment.total_expenses = sum(exp.amount for exp in investment.expense_ids)

    @api.depends('partnership_ids.down_payment')
    def _compute_partnerships(self):
        """Calculate total confirmed or distributed partnerships amount"""
        for investment in self:
            investment.total_partnerships = sum(inv.down_payment for inv in investment.partnership_ids)

    @api.depends('partnership_ids.percentage')
    def _compute_total_partnerships_percentage(self):
        for investment in self:
            investment.total_partnerships_percentage = sum(inv.percentage for inv in investment.partnership_ids)
            
# =========================== Action Functions ===========================

    def action_view_partnerships(self):
        """View investment partnerships"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('investment partnerships'),
            'res_model': 'real.estate.partnership',
            'view_mode': 'tree,form',
            'domain': [('investment_id', '=', self.id)],
            'context': {'default_investment_id': self.id,},
        }

    def action_view_expenses(self):
        """View property expenses"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Expenses'),
            'res_model': 'real.estate.expense',
            'view_mode': 'tree,form',
            'domain': [('investment_id', '=', self.id)],
            'context': {'default_investment_id': self.id,'default_expense_type': 'investment',},
        }

    def action_view_purchased_properties(self):
        """View Purchased Properties"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Child Properties'),
            'res_model': 'real.estate.property',
            'view_mode': 'tree,form',
            'domain': [('investment_id', '=', self.id),('is_purchased','=', True)],
            'context': {'default_investment_id': self.id},
        }

    def action_view_sold_properties(self):
        """View Sold Properties"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sold Properties'),
            'res_model': 'real.estate.property',
            'view_mode': 'tree,form',
            'domain': [('investment_id', '=', self.id),('is_purchased','=', False)],
            'context': {'default_investment_id': self.id},
        }

    def action_view_investment_profit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Profits'),
            'res_model': 'real.estate.sale.line',
            'view_mode': 'tree,form',
            'domain': [('investment_id', '=', self.id)],
        }

    def action_create_partnership(self):
        # Open partnership creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create partnership'),
            'res_model': 'real.estate.partnership',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_investment_id': self.id,
            },
        }

    def action_add_expense(self):
        
        # Open expense creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Expense'),
            'res_model': 'real.estate.expense',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_investment_id': self.id,
                'default_expense_type': 'investment',
            },
        }


    def action_create_purchased_property(self):
        """Create Purchased Properties"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Purchase Property'),
            'res_model': 'real.estate.property',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_investment_id': self.id,
                'default_is_purchased':True,
                'default_name': _('%s - Purchased Property %s') % (self.code, len(self.purchased_properties_ids) + 1),
                'default_status': 'confirmed',
                'default_property_date': fields.Date.today(),
            },
        }

    def action_create_sold_property(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Sale Property'),
            'res_model': 'real.estate.property',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_investment_id': self.id,
                'default_name': _('%s - Sold Property %s') % (self.code, len(self.sold_properties_ids) + 1),
                'default_total_area': self.remaining_area,
            },
        }

    def action_close_investment(self):
        for investment in self:
            investment.status = 'closed'
            investment.close_date = fields.Date.today()

    def action_reopen_investment(self):
        for investment in self:
            investment.status = 'opening'
            investment.close_date = None

    def action_restructuring_investment(self):
        self.ensure_one()

        draft_sold_properties = self.sold_properties_ids.filtered(lambda property: property.status == 'draft')
        for property in draft_sold_properties:
            if property.property_price == 0:
                raise ValidationError(_(f'Property {property.name} its property price must be greater than zero.'))

            property.write({
                'is_conversion': True,
                'property_date': fields.Date.today(),
                'contact_id': self.env.company.partner_id.id,
                'down_payment': property.property_price,
                })
            property.action_confirmed_sold_property()

            investment = self.create({
                'name': _('ٌRestructuring - %s') % (self.name),
                'open_date': fields.Date.today(),
                'investment_type': self.investment_type,
                'area_unit': self.area_unit,
                'investment_method': self.investment_method,
                'city_id': self.city_id.id,
                'address': self.address,
                
            })

            self.env['real.estate.property'].create({
                'investment_id': investment.id,
                'name':  _('ٌRestructuring - %s') % (property.name),
                'status': 'confirmed',
                'property_date': fields.Date.today(),
                'property_price': property.property_price,
                'down_payment': property.property_price,
                'current_value': property.property_price,
                'total_area': property.total_area,
                'contact_id': property.contact_id.id,
                'is_purchased': True,
                'north_boundary': property.north_boundary,
                'south_boundary': property.south_boundary,
                'east_boundary': property.east_boundary,
                'west_boundary': property.west_boundary,
            })

            records = []
            for partnership in self.partnership_ids:
                amount = (property.property_price * partnership.percentage) / 100
                records.append({
                    'partner_id': partnership.partner_id.id,
                    'investment_id': investment.id,
                    'percentage': partnership.percentage if partnership.investment_method == 'percentage' else 0.0,
                    'payment_line_ids':[(0, 0, {
                    'payment_date': fields.Date.today(),
                    'amount': amount,    
                    })],
                })
            self.env['real.estate.partnership'].create(records)
            
        self.is_restructured = True
        self.status = 'closed'
        self.close_date = fields.Date.today()

    # ============== Logic Functions  ========================
    
    
