# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RealEstatePartnerExitLines(models.Model):
    _name = 'real.estate.partner.exit.lines'
    _description = 'Real Estate Partner Exit Profit Distribution Lines'
    _order = 'id'

    name = fields.Char(string='Description', compute='_compute_name', store=True, readonly=True)
    # Relations
    exit_id = fields.Many2one('real.estate.partner.exit', string='Partner Exit', required=True, ondelete='cascade')
    partner_id = fields.Many2one('real.estate.partner', string='Partner', required=True, ondelete='restrict')
    property_id = fields.Many2one('real.estate.property', string='Property', ondelete='restrict', related='exit_id.property_id', store=True, readonly=True)
    exit_date = fields.Date(string='Exit Date', related='exit_id.exit_date', store=True, readonly=True)
    # Investment Details
    investment_percentage = fields.Float(string='Investment Percentage (%)', required=True, digits=(5, 2))
    original_investment_amount = fields.Float(string='Original Investment Amount', required=True, digits=(16, 2))
    
    # Profit Distribution Details
    profit_amount = fields.Float(string='Profit Amount', required=True, digits=(16, 2))
    is_exiting_partner = fields.Boolean(string='Is Exiting Partner', default=False)

    # ============================ Compute Methods ============================
    @api.depends('partner_id', 'exit_id')
    def _compute_name(self):
        for line in self:
            if line.partner_id and line.exit_id:
                line.name = f'Profit-Exit-{line.partner_id.name} - {line.exit_id.name}'
            else:
                line.name = '/'

    # ============================ Validation Functions ============================
    def validate_exit_line_partner(self):
        if self.partner_id.status != 'active' or self.partner_id.active == False:
            raise ValidationError(_('The old partner (%s) is not active .', self.partner_id.name))