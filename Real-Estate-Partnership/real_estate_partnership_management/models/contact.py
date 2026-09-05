# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from random import randint


class RealEstateContact(models.Model):
    _name = 'real.estate.contact'
    _description = 'Real Estate Contact (Seller/Payee)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Contact Name', required=True, tracking=True)
    code = fields.Char(string='Contact Code', required=True, copy=False, default=lambda self: _('New'))
    color = fields.Integer(string='Color', default=_get_default_color)
    
    # Contact Information
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    address = fields.Text(string='Address', tracking=True)
    national_id = fields.Char(string='National ID', tracking=True)
    nickname = fields.Char(string='Nickname', tracking=True)
    workplace = fields.Char(string='Workplace', tracking=True)
    
    # Location Information
    city_id = fields.Many2one('real.estate.city', string='City', tracking=True)
    state_id = fields.Many2one('real.estate.state', string='State/Province', tracking=True)
    country_id = fields.Many2one('res.country', string='Country', tracking=True)
    
    # Contact Types (Boolean fields)
    is_seller = fields.Boolean(string='Seller', compute='_compute_is_seller', tracking=True, readonly=True, store=True, help="This contact can be a seller of properties")
    is_payee = fields.Boolean(string='Payee', compute='_compute_is_payee', tracking=True, readonly=True, store=True, help="This contact can receive payments for expenses")
    is_buyer = fields.Boolean(string='Buyer', compute='_compute_is_buyer', tracking=True, readonly=True, store=True, help="This contact can buy properties")
    
    # Status
    active = fields.Boolean(string='Active', default=True, tracking=True)
    # Notes
    notes = fields.Text(string='Notes')
    # Related Data
    property_ids = fields.One2many('real.estate.property', 'seller_id', string='Properties Sold')
    property_sale_ids = fields.One2many('real.estate.property.sale', 'buyer_contact_id' ,string='Properties Bought')
    expense_ids = fields.One2many('real.estate.expense', 'paid_to_contact_id', string='Expenses Paid')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.contact') or _('New')
        return super(RealEstateContact, self).create(vals_list)

    # =========================== Compute Functions ===========================

    @api.depends('property_ids.seller_id')
    def _compute_is_seller(self):
        for contact in self:
            contact.is_seller = bool(contact.property_ids)

    @api.depends('property_sale_ids.buyer_contact_id')
    def _compute_is_buyer(self):
        for contact in self:
            contact.is_buyer = bool(contact.property_sale_ids)

    @api.depends('expense_ids.paid_to_contact_id')
    def _compute_is_payee(self):
        for contact in self:
            contact.is_payee = bool(contact.expense_ids)

    # =========================== Action Functions ===========================

    def action_view_property_sales(self):
        """View property sales where this contact is the buyer"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Property Sales'),
            'res_model': 'real.estate.property.sale',
            'view_mode': 'tree,form',
            'domain': [('buyer_contact_id', '=', self.id)],
            'context': {'default_buyer_contact_id': self.id},
        }

    def action_view_properties(self):
        """View properties sold by this contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Properties Sold'),
            'res_model': 'real.estate.property',
            'view_mode': 'tree,form',
            'domain': [('seller_id', '=', self.id)],
            'context': {'default_seller_id': self.id},
        }

    def action_view_expenses(self):
        """View expenses paid to this contact"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses Paid'),
            'res_model': 'real.estate.expense',
            'view_mode': 'tree,form',
            'domain': [('paid_to_contact_id', '=', self.id)],
            'context': {'default_paid_to_contact_id': self.id},
        }

    # =========================== Constrains Functions ===========================

    @api.constrains('email')
    def _check_email(self):
        for contact in self:
            if contact.email and '@' not in contact.email:
                raise ValidationError(_('Please enter a valid email address.'))

    @api.constrains('phone')
    def _check_phone(self):
        for contact in self:
            if contact.phone and not contact.phone.replace(' ', '').replace('-', '').isdigit():
                raise ValidationError(_('Phone number should contain only digits.'))

    @api.constrains('name')
    def _check_unique_name(self):
        for contact in self:
            if contact.name:
                existing = self.search([('name', '=ilike', contact.name), ('id', '!=', contact.id)])
                if existing:
                    raise ValidationError(_('Contact name must be unique. A contact with this name already exists.'))

    @api.constrains('national_id')
    def _check_unique_national_id(self):
        for contact in self:
            if contact.national_id:
                existing = self.search([('national_id', '=', contact.national_id), ('id', '!=', contact.id)])
                if existing:
                    raise ValidationError(_('National ID must be unique. A contact with this National ID already exists.'))
