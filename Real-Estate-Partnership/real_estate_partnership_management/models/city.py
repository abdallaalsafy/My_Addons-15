# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstateCity(models.Model):
    _name = 'real.estate.city'
    _description = 'Real Estate City'
    _order = 'name asc'

    name = fields.Char(string='City Name', required=True)
    code = fields.Char(string='City Code', help='City code for quick identification')
    state_id = fields.Many2one('real.estate.state', string='State/Province')
    country_id = fields.Many2one('res.country', string='Country')
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')

    @api.constrains('name')
    def _check_name(self):
        for city in self:
            if not city.name or not city.name.strip():
                raise ValidationError(_('City name is required.'))

    @api.constrains('code')
    def _check_code(self):
        for city in self:
            if city.code and self.search([('code', '=', city.code), ('id', '!=', city.id)]):
                raise ValidationError(_('City code must be unique.'))

    def name_get(self):
        result = []
        for city in self:
            name = city.name
            if city.state_id:
                name = f"{name}, {city.state_id.name}"
            if city.country_id:
                name = f"{name}, {city.country_id.name}"
            result.append((city.id, name))
        return result
