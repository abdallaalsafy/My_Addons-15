# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstateState(models.Model):
    _name = 'real.estate.state'
    _description = 'Real Estate State/Province'
    _order = 'name asc'

    name = fields.Char(string='State/Province Name', required=True)
    code = fields.Char(string='State Code', help='State code for quick identification')
    country_id = fields.Many2one('res.country', string='Country', required=True)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')

    @api.constrains('name')
    def _check_name(self):
        for state in self:
            if not state.name or not state.name.strip():
                raise ValidationError(_('State name is required.'))

    @api.constrains('code')
    def _check_code(self):
        for state in self:
            if state.code and self.search([('code', '=', state.code), ('id', '!=', state.id)]):
                raise ValidationError(_('State code must be unique.'))

    def name_get(self):
        result = []
        for state in self:
            name = state.name
            if state.country_id:
                name = f"{name}, {state.country_id.name}"
            result.append((state.id, name))
        return result
