# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

# Sale Line Model
class RealEstateSaleLine(models.Model):
    _name = 'real.estate.sale.line'
    _description = 'Real Estate Sale Line'


    property_id = fields.Many2one('real.estate.property', string='Property',)
    property_date = fields.Date(related='property_id.property_date', store=True)
    investment_id = fields.Many2one(related='property_id.investment_id', store=True,)
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, index=True, ondelete='restrict')
    profit_amount = fields.Monetary(string='Profit Amount', required=True, currency_field='company_currency')
