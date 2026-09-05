# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

# Sale Line Model
class RealEstatePropertySaleLine(models.Model):
    _name = 'real.estate.property.sale.line'
    _description = 'Real Estate Property Sale Line'

    sale_id = fields.Many2one('real.estate.property.sale', string='Sale', required=True, index=True, ondelete='cascade')
    sale_date = fields.Date(related='sale_id.sale_date', string='Sale Date', store=True)
    property_id = fields.Many2one('real.estate.property', string='Property', related='sale_id.property_id', store=True, readonly=True)
    partner_id = fields.Many2one('real.estate.partner', string='Partner', required=True, index=True, ondelete='restrict')
    # Investment Details
    investment_id = fields.Many2one('real.estate.property.investment', string='Investment', ondelete='restrict',
                                    readonly=True)
    investment_amount = fields.Float(string='Investment Amount', required=True)
    investment_percentage = fields.Float(string='Investment %', required=True)
    # Profit Details
    profit_amount = fields.Float(string='Profit Amount', required=True)
