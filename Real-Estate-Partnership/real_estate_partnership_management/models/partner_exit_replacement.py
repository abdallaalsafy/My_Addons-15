# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstatePartnerExitReplacement(models.Model):
    _name = 'real.estate.partner.exit.replacement'
    _description = 'Real Estate Partner Exit - Replacement Partners'
    _order = 'exit_id, id'

    name = fields.Char(string='Description', compute='_compute_name', store=True, readonly=True)
    
    # Relations
    exit_id = fields.Many2one('real.estate.partner.exit', string='Partner Exit', required=True, ondelete='cascade')
    partner_id = fields.Many2one('real.estate.partner', string='Replacement Partner', required=True, ondelete='restrict',
                                 domain="[('status', '=', 'active')]")

    # Replacement Details
    partner_type = fields.Selection([
        ('new', 'New Investment'),
        ('existing', 'Same Investment'),
    ], string='Partner Type', compute='_compute_partner_type', store=True, readonly=True)

    replacement_percentage = fields.Float(string='Replacement Percentage (%)', required=True, digits=(5, 2))

    investment_id = fields.Char(string='Investment', compute='_compute_partner_type', store=True, readonly=True)
    investment_percentage = fields.Float(string='Investment Percentage (%)', compute='_compute_partner_type',
                                         store=True, readonly=True)

    # ============================ Compute Methods ============================
    @api.depends('partner_id', 'exit_id')
    def _compute_name(self):
        for line in self:
            if line.partner_id and line.exit_id:
                line.name = f'Replacement - {line.partner_id.name} - {line.exit_id.name}'
            else:
                line.name = '/'

    @api.depends('partner_id', 'exit_id.property_id')
    def _compute_partner_type(self):
        for line in self:
            if line.partner_id and line.exit_id.property_id:
                # Check if partner has existing investment in this property
                existing_investment = self.env['real.estate.property.investment'].search([
                    ('partner_id', '=', line.partner_id.id),
                    ('property_id', '=', line.exit_id.property_id.id),
                    ('status', '=', 'confirmed'),
                ], limit=1)
                if existing_investment:
                    line.partner_type = 'existing'
                    line.investment_id = existing_investment.name
                    line.investment_percentage = existing_investment.percentage
                else:
                    line.partner_type = 'new'
                    exit.investment_id = False
                    exit.investment_percentage = 0.0
            else:
                line.partner_type = 'new'
                exit.investment_id = False
                exit.investment_percentage = 0.0

    # ============================ Constrains Methods ============================
    @api.constrains('partner_id', 'exit_id')
    def _check_unique_partner(self):
        for line in self:
            duplicates = self.search([
                ('exit_id', '=', line.exit_id.id),
                ('partner_id', '=', line.partner_id.id),
                ('id', '!=', line.id)
            ])
            if duplicates:
                raise ValidationError(_('Partner %s is already added to this exit.') % line.partner_id.name)

    @api.constrains('replacement_percentage')
    def _check_replacement_percentage(self):
        for line in self:
            if line.replacement_percentage <= 0:
                raise ValidationError(_('Replacement percentage must be positive.'))

    # ============================ Validation Functions ============================
    def validate_replacement_partner_status_investment(self):
        if self.partner_id.status != 'active' or self.partner_id.active == False:
            raise ValidationError(_('The old partner (%s) is not active .', self.partner_id.name))

        if self.investment_id:
            invest = self.partner_id.investment_ids.search([('name', '=', self.investment_id)])
            if not invest:
                raise ValidationError(
                    _('The old partner (%s) has no confirmed investment in this property.', self.partner_id.name))

            check_new = self.partner_type == 'new' and (invest.percentage != self.replacement_percentage or invest.status != 'confirmed')
            check_existing = self.partner_type == 'existing' and (
                    invest.percentage != self.investment_percentage + self.replacement_percentage or invest.status != 'confirmed')

            if check_existing or check_new:
                raise ValidationError(
                    _('The invest of old partner (%s) is not equal to the exit percentage .', self.partner_id.name))

