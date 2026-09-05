# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

# Sale Line Model
class RealEstatePropertySaleLine(models.Model):
    _name = 'real.estate.property.sale.line'
    _description = 'Real Estate Property Sale Line'


    contract_id = fields.Many2one('real.estate.property', string='Contract',)
    contract_date = fields.Date(related='contract_id.contract_date', store=True)
    deal_id = fields.Many2one(related='contract_id.deal_id', store=True,)

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, index=True, ondelete='restrict')
    profit_amount = fields.Float(string='Profit Amount', required=True)
