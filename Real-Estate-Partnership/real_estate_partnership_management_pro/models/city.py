# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstateCity(models.Model):
    _name = 'real.estate.city'
    _description = 'Real Estate City'
    _order = 'name asc'

    name = fields.Char(string='City Name', required=True)

    @api.constrains('name')
    def _check_name_city(self):
        for city in self:
            if not city.name or not city.name.strip():
                raise ValidationError(_('City name is required.'))

            city = self.search([('name', '=', city.name), ('id', '!=', city.id)])
            if city:
                raise ValidationError(_('City name must be unique.'))

