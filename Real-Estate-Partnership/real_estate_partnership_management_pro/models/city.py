# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstateCity(models.Model):
    _name = 'real.estate.city'
    _description = 'Real Estate City'
    _order = 'name asc'

    name = fields.Char(string='City Name', required=True)

    investment_ids = fields.One2many('real.estate.investment', 'city_id', string='Investments')
    property_ids = fields.One2many('real.estate.property', 'city_id', string='Properties')
    investment_count = fields.Integer(string='Investments Count', compute='_compute_investment_count', store=True)
    property_count = fields.Integer(string='Properties Count', compute='_compute_property_count', store=True)
    purchased_property_count = fields.Integer(string='Purchased Properties Count', compute='_compute_property_count', store=True)
    sold_property_count = fields.Integer(string='Sold Properties Count', compute='_compute_property_count', store=True)

    @api.depends('investment_ids')
    def _compute_investment_count(self):
        for city in self:
            city.investment_count = len(city.investment_ids)

    @api.depends('property_ids', 'property_ids.is_purchased')
    def _compute_property_count(self):
        for city in self:
            city.property_count = len(city.property_ids)
            city.purchased_property_count = len(city.property_ids.filtered('is_purchased'))
            city.sold_property_count = city.property_count - city.purchased_property_count
            
    @api.constrains('name')
    def _check_name_city(self):
        for city in self:
            if not city.name.strip():
                raise ValidationError(_('City name is required.'))

            city = self.search([('name', '=', city.name), ('id', '!=', city.id)])
            if city:
                raise ValidationError(_('City name must be unique.'))

