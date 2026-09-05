# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint
from .property import RealEstateProperty as property

class RealEstateDeal(models.Model):
    _name = 'real.estate.deal'
    _description = 'Real Estate Deal'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    def _get_default_color(self):
        return randint(1, 11)


    name = fields.Char(string='Property Name', required=True, tracking=True, index=True)
    code = fields.Char(string='Property Code', required=True, copy=False, default=lambda self: _('New'), index=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    open_date = fields.Date(string='Open Date', required=True, default=fields.Date.today, tracking=True)
    close_date = fields.Date(string='Close Date', readonly=True, tracking=True)
    is_restructured = fields.Boolean(string='Restructured', default=False, tracking=True)
    
    investment_method = fields.Selection([
            ('percentage', 'Percentage'),
            ('amount', 'Amount'),
        ], string='Investment Method', default='percentage', tracking=True,
           help='Determines how investments are recorded for this property')
    status = fields.Selection([
                ('opening', 'Opening'),
                ('closed', 'Closed'),
            ], string='Status', default='opening', tracking=True, index=True)
    
    deal_type = fields.Selection(property._SELECTION_PROPERTY_TYPE, string='Deal Type', required=True, index=True)
    area_unit = fields.Selection(property._SELECTION_AREA_UNIT, string='Area Unit', required=True, index=True, help='Unit of measurement for the property area')
    # Location Information
    city_id = fields.Many2one('real.estate.city', string='City', tracking=True, index=True)
    address = fields.Text(string='Full Address', tracking=True)
    # Property Boundaries
    north_boundary = fields.Text(string='North Boundary', compute='_compute_purchased_contract_boundary', store=True, readonly=False, help='What borders the property from the north')
    south_boundary = fields.Text(string='South Boundary', compute='_compute_purchased_contract_boundary', store=True, readonly=False, help='What borders the property from the south')
    east_boundary = fields.Text(string='East Boundary', compute='_compute_purchased_contract_boundary', store=True, readonly=False, help='What borders the property from the east')
    west_boundary = fields.Text(string='West Boundary', compute='_compute_purchased_contract_boundary', store=True, readonly=False, help='What borders the property from the west')
    # Room Details
    built_area = fields.Float(string='Built Area', tracking=True, compute='_compute_purchased_contract_rooms', store=True, help='Built area of the property (used for area ratio calculations)')
    number_of_floors = fields.Integer(string='Number of Floors', tracking=True, compute='_compute_purchased_contract_rooms', store=True, help='Number of floors in the property')
    total_rooms = fields.Integer(string='Total Rooms', tracking=True,  compute='_compute_purchased_contract_rooms', store=True, help='Total number of rooms in the property')
    bedrooms = fields.Integer(string='Bedrooms', tracking=True, compute='_compute_purchased_contract_rooms', store=True, help='Number of bedrooms in the property')
    bathrooms = fields.Integer(string='Bathrooms', tracking=True, compute='_compute_purchased_contract_rooms', store=True, help='Number of bathrooms in the property')
    kitchens = fields.Integer(string='Kitchens', tracking=True, compute='_compute_purchased_contract_rooms', store=True, help='Number of kitchens in the property')
    living_rooms = fields.Integer(string='Living Rooms', tracking=True, compute='_compute_purchased_contract_rooms', store=True, help='Number of living rooms in the property')
    # Area and Units
    total_area = fields.Float(string='Total Area', compute='_compute_total_area', store=True,)
    sold_area = fields.Float(string='Sold Area', compute='_compute_sold_remaining_area', store=True,)
    remaining_area = fields.Float(string='Remaining Area', compute='_compute_sold_remaining_area', store=True,)
    # Financial Information
    total_current_value = fields.Float(string='Total Current Value', compute='_compute_total_current_value', store=True)
    total_deal_cost = fields.Float(string='Total Deal Cost', compute='_compute_total_deal_cost', store=True)
    total_cost_before_sold = fields.Float(string='Total Purchase Cost', compute='_compute_total_deal_cost', store=True)
    total_expenses = fields.Float(string='Total Expenses', compute='_compute_deal_expenses', store=True)
    total_investments = fields.Float(string='Total Investments', compute='_compute_investments', store=True)
    total_investments_percentage = fields.Float(string='Total Percentage', compute='_compute_total_investments_percentage', store=True)
    
    # Counts for related records
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
    investment_count = fields.Integer(string='Investment Count', compute='_compute_investment_count')
    attachment_count = fields.Integer(string='Document Count', compute='_compute_attachment_count')
    purchased_contracts_count = fields.Integer(string='Purchased Contracts Count', compute='_compute_contracts_count')
    sold_contracts_count = fields.Integer(string='Sold Contracts Count', compute='_compute_contracts_count')
    confirmed_sold_contracts_count = fields.Integer(string='ConfirmedSold Contracts Count', compute='_compute_contracts_count')
    draft_sold_contracts_count = fields.Integer(string='ConfirmedSold Contracts Count', compute='_compute_contracts_count', store=True)
    profit_count = fields.Integer(string='Profit Count', compute='_compute_profit_count')
    
    # Notes and Documents
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', help='Upload property documents, images, contracts, etc.')
    
    # Related Data
    purchased_contracts_ids = fields.One2many('real.estate.property', 'deal_id', string='Purchased Contracts', domain=[('is_purchased', '=', True)])
    sold_contracts_ids = fields.One2many('real.estate.property', 'deal_id', string='Sold Contracts', domain=[('is_purchased', '=', False)])
    investment_ids = fields.One2many('real.estate.property.investment', 'deal_id', string='Investments')
    expense_ids = fields.One2many('real.estate.expense', 'deal_id', string='Expenses')
    sale_line_ids = fields.One2many('real.estate.property.sale.line', 'deal_id', string='Sale Lines')

    # ====================== Built-in methods =================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.deal') or _('New')

        deals = super(RealEstateDeal, self).create(vals_list)
        return deals

    def write(self, vals):
        result = super(RealEstateDeal, self).write(vals)

        if 'investment_method' in vals:
            self.env['real.estate.investment.payment'].get_percentage_value(self.investment_ids)
        return result

    def unlink(self):
        for deal in self:
            if deal.status == 'closed':
                raise ValidationError(_('You cannot delete an closed deal'))
            # Because Partner need investment_ids in compute Field
            # Because this line compute field cannot be computedS
            deal.investment_ids.unlink()
        return super(RealEstateDeal, self).unlink()

    # =========================== Compute Functions ===========================

    def _compute_contracts_count(self):
        for deal in self:
            deal.purchased_contracts_count = len(deal.purchased_contracts_ids)
            deal.sold_contracts_count = len(deal.sold_contracts_ids)
            deal.confirmed_sold_contracts_count = len([contract for contract in deal.sold_contracts_ids if contract.status == 'confirmed'])
            deal.draft_sold_contracts_count = len([contract for contract in deal.sold_contracts_ids if contract.status == 'draft'])

    def _compute_expense_count(self):
        for deal in self:
            deal.expense_count = len(deal.expense_ids)

    def _compute_investment_count(self):
            for deal in self:
                deal.investment_count = len(deal.investment_ids)

    def _compute_attachment_count(self):
        for deal in self:
            deal.attachment_count = len(deal.attachment_ids)

    def _compute_profit_count(self):
        for deal in self:
            deal.profit_count = len(deal.sale_line_ids)
    #-------------------------------------------------

    @api.depends('purchased_contracts_ids.area_unit')
    def _compute_purchased_contract_area_unit(self):
        for deal in self:
            if deal.purchased_contracts_ids:
                # Assuming the first purchased contract's area unit is representative
                first_contract = deal.purchased_contracts_ids[0]
                deal.area_unit = first_contract.area_unit
            else:
                deal.area_unit = False

    @api.depends('purchased_contracts_ids.built_area', 'purchased_contracts_ids.number_of_floors', 'purchased_contracts_ids.total_rooms', 'purchased_contracts_ids.bedrooms', 'purchased_contracts_ids.bathrooms', 'purchased_contracts_ids.kitchens', 'purchased_contracts_ids.living_rooms')
    def _compute_purchased_contract_rooms(self):
        for deal in self:
            # If there are purchased contracts, sum their room specifications; otherwise, set to zero
            if deal.purchased_contracts_ids:
                deal.built_area = sum(contract.built_area for contract in deal.purchased_contracts_ids)
                deal.number_of_floors = sum(contract.number_of_floors for contract in deal.purchased_contracts_ids)
                deal.total_rooms = sum(contract.total_rooms for contract in deal.purchased_contracts_ids)
                deal.bedrooms = sum(contract.bedrooms for contract in deal.purchased_contracts_ids)
                deal.bathrooms = sum(contract.bathrooms for contract in deal.purchased_contracts_ids)
                deal.kitchens = sum(contract.kitchens for contract in deal.purchased_contracts_ids)
                deal.living_rooms = sum(contract.living_rooms for contract in deal.purchased_contracts_ids)
            else:
                deal.built_area = 0
                deal.number_of_floors = 0
                deal.total_rooms = 0
                deal.bedrooms = 0
                deal.bathrooms = 0
                deal.kitchens = 0
                deal.living_rooms = 0

    @api.depends('purchased_contracts_ids.north_boundary', 'purchased_contracts_ids.south_boundary', 'purchased_contracts_ids.east_boundary', 'purchased_contracts_ids.west_boundary')
    def _compute_purchased_contract_boundary(self):
        for deal in self:
            if len(deal.purchased_contracts_ids) == 1:
                # Assuming the first purchased contract's boundaries are representative
                first_contract = deal.purchased_contracts_ids[0]
                deal.north_boundary = first_contract.north_boundary
                deal.south_boundary = first_contract.south_boundary
                deal.east_boundary = first_contract.east_boundary
                deal.west_boundary = first_contract.west_boundary
            else:
                deal.north_boundary = False
                deal.south_boundary = False
                deal.east_boundary = False
                deal.west_boundary = False

    @api.depends('purchased_contracts_ids.current_value')
    def _compute_total_current_value(self):
        for deal in self:
            if deal.purchased_contracts_ids:
                deal.total_current_value = sum(contract.current_value for contract in deal.purchased_contracts_ids)
            else:
                deal.total_current_value = 0.0

    @api.depends('purchased_contracts_ids.total_cost', 'sold_contracts_ids.total_expenses', 'total_expenses')
    def _compute_total_deal_cost(self):
        for deal in self:
            total_purchase_contracts_cost = sum(contract.total_cost for contract in deal.purchased_contracts_ids)
            total_sold_contracts_expenses = sum(contract.total_expenses for contract in deal.sold_contracts_ids)
            total_cost_before_sold = total_purchase_contracts_cost + deal.total_expenses
            deal.total_deal_cost = total_cost_before_sold + total_sold_contracts_expenses
            deal.total_cost_before_sold = total_cost_before_sold

    @api.depends('purchased_contracts_ids.total_area')
    def _compute_total_area(self):
        for deal in self:
            if deal.purchased_contracts_ids:
                deal.total_area = sum(contract.total_area for contract in deal.purchased_contracts_ids)
            else:
                deal.total_area = 0.0

    @api.depends('sold_contracts_ids.total_area', 'total_area')
    def _compute_sold_remaining_area(self):
        for deal in self:
            deal.sold_area = sum(contract.total_area for contract in deal.sold_contracts_ids)
            deal.remaining_area = deal.total_area - deal.sold_area

    @api.depends('expense_ids.amount')
    def _compute_deal_expenses(self):
        """ Calculate total confirmed or paid expenses amount"""
        for deal in self:
            deal.total_expenses = sum(exp.amount for exp in deal.expense_ids)

    @api.depends('investment_ids.down_payment')
    def _compute_investments(self):
        """Calculate total confirmed or distributed investments amount"""
        for deal in self:
            deal.total_investments = sum(inv.down_payment for inv in deal.investment_ids)

    @api.depends('investment_ids.percentage')
    def _compute_total_investments_percentage(self):
        for deal in self:
            deal.total_investments_percentage = sum(inv.percentage for inv in deal.investment_ids)

    # =========================== Constraints Functions ===========================

    # @api.constrains('investment_method')
    # def _check_investment_method_change(self):
    #     """Prevent changing investment method when investments exist"""
    #     for deal in self:
    #         if deal.investment_count > 0:
    #             raise ValidationError(
    #                 _('Cannot change investment method for property "%s" while there are existing investments. '
    #                   'Please remove all investments before changing the investment method.') %
    #                 (deal.name or deal.code)
                # )
            
# =========================== Action Functions ===========================

    def action_view_investments(self):
        """View deal investments"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deal Investments'),
            'res_model': 'real.estate.property.investment',
            'view_mode': 'tree,form',
            'domain': [('deal_id', '=', self.id)],
            'context': {'default_deal_id': self.id,},
        }

    def action_view_expenses(self):
        """View property expenses"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Expenses'),
            'res_model': 'real.estate.expense',
            'view_mode': 'tree,form',
            'domain': [('deal_id', '=', self.id)],
            'context': {'default_deal_id': self.id,'default_expense_type': 'investment',},
        }

    def action_view_purchased_contracts(self):
        """View Purchased Contracts"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Child Properties'),
            'res_model': 'real.estate.property',
            'view_mode': 'tree,form',
            'domain': [('deal_id', '=', self.id),('is_purchased','=', True)],
            'context': {'default_deal_id': self.id},
        }

    def action_view_sold_contracts(self):
        """View Sold Contracts"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sold Contracts'),
            'res_model': 'real.estate.property',
            'view_mode': 'tree,form',
            'domain': [('deal_id', '=', self.id),('is_purchased','=', False)],
            'context': {'default_deal_id': self.id},
        }

    def action_view_deal_profit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract Profits'),
            'res_model': 'real.estate.property.sale.line',
            'view_mode': 'tree,form',
            'domain': [('deal_id', '=', self.id)],
        }

    def action_create_investment(self):
        # Open investment creation form with readonly property field
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Investment'),
            'res_model': 'real.estate.property.investment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_deal_id': self.id,
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
                'default_deal_id': self.id,
                'default_expense_type': 'investment',
            },
        }


    def action_create_purchased_contract(self):
        """Create Purchased Contracts"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Child Property'),
            'res_model': 'real.estate.property',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_deal_id': self.id,
                'default_is_purchased':True,
                'default_name': _('%s - Purchased Contract %s') % (self.code, len(self.purchased_contracts_ids) + 1),
                'default_status': 'confirmed',
                'default_purchase_date': fields.Date.today(),
            },
        }

    def action_create_sold_contract(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Sale Contract'),
            'res_model': 'real.estate.property',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_deal_id': self.id,
                'default_name': _('%s - PurSold Contract %s') % (self.code, len(self.sold_contracts_ids) + 1),
                'default_total_area': self.remaining_area,
            },
        }

    def action_close_deal(self):
        for deal in self:
            deal.status = 'closed'
            deal.close_date = fields.Date.today()

    def action_reopen_deal(self):
        for deal in self:
            deal.status = 'opening'
            deal.close_date = None

    def action_restructuring_deal(self):
        self.ensure_one()

        draft_sold_contracts = self.sold_contracts_ids.filtered(lambda contract: contract.status == 'draft')
        for contract in draft_sold_contracts:
            if contract.contract_price == 0:
                raise ValidationError(_(f'Contract {contract.name} its contract price must be greater than zero.'))

            contract.write({
                'is_conversion': True,
                'contract_date': fields.Date.today(),
                'contact_id': self.env.company.partner_id.id,
                'down_payment': contract.contract_price,
                })
            contract.action_confirmed_sold_contract()

            deal = self.create({
                'name': _('ٌRestructuring - %s') % (self.name),
                'open_date': fields.Date.today(),
                'deal_type': self.deal_type,
                'area_unit': self.area_unit,
                'investment_method': self.investment_method,
                'city_id': self.city_id.id,
                'address': self.address,
                
            })

            self.env['real.estate.property'].create({
                'deal_id': deal.id,
                'name':  _('ٌRestructuring - %s') % (contract.name),
                'status': 'confirmed',
                'contract_date': fields.Date.today(),
                'contract_price': contract.contract_price,
                'down_payment': contract.contract_price,
                'current_value': contract.contract_price,
                'total_area': contract.total_area,
                'contact_id': contract.contact_id.id,
                'is_purchased': True,
                'north_boundary': contract.north_boundary,
                'south_boundary': contract.south_boundary,
                'east_boundary': contract.east_boundary,
                'west_boundary': contract.west_boundary,
            })

            records = []
            for partnership in self.investment_ids:
                amount = (contract.contract_price * partnership.percentage) / 100
                records.append({
                    'partner_id': partnership.partner_id.id,
                    'deal_id': deal.id,
                    'percentage': partnership.percentage if partnership.investment_method == 'percentage' else 0.0,
                    'payment_line_ids':[(0, 0, {
                    'payment_date': fields.Date.today(),
                    'amount': amount,    
                    })],
                })
            self.env['real.estate.property.investment'].create(records)
            
        self.is_restructured = True
        self.status = 'closed'
        self.close_date = fields.Date.today()

    # ============== Logic Functions  ========================
    
    
