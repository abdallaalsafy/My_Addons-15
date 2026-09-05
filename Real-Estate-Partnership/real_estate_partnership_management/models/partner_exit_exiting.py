# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstatePartnerExitExiting(models.Model):
    _name = 'real.estate.partner.exit.exiting'
    _description = 'Real Estate Partner Exit - Exiting Partners'
    _order = 'exit_id, id'

    name = fields.Char(string='Description', compute='_compute_name', store=True, readonly=True)
    # Relations
    exit_id = fields.Many2one('real.estate.partner.exit', string='Partner Exit', required=True, ondelete='cascade')
    partner_id = fields.Many2one('real.estate.partner', string='Exiting Partner', required=True, ondelete='restrict', domain="[('status', '=', 'active')]")

    # Exit Details
    exit_type = fields.Selection([
        ('full', 'Full Exit'),
        ('partial', 'Partial Exit'),
    ], string='Exit Type', compute='_compute_exit_type', store=True, readonly=True)

    investment_id = fields.Char(string='Investment', compute='_compute_investment_info', store=True, readonly=True)
    investment_percentage = fields.Float(string='Investment Percentage (%)',  compute='_compute_investment_info', store=True, readonly=True)
    exit_percentage = fields.Float(string='Exit Percentage (%)', required=True,)

    # ============================ Compute Methods ============================

    @api.depends('partner_id', 'exit_id')
    def _compute_name(self):
        for line in self:
            if line.partner_id and line.exit_id:
                line.name = f'Exit - {line.partner_id.name} - {line.exit_id.name}'
            else:
                line.name = '/'

    @api.depends('exit_percentage', 'investment_percentage')
    def _compute_exit_type(self):
        for line in self:
            if line.exit_percentage >= line.investment_percentage:
                line.exit_type = 'full'
            else:
                line.exit_type = 'partial'

    @api.depends('partner_id', 'exit_id.property_id')
    def _compute_investment_info(self):
        for exit in self:
            if exit.partner_id and exit.exit_id.property_id:
                invest = exit.partner_id.investment_ids.search([('status', '=', 'confirmed'),('property_id', '=', exit.exit_id.property_id.id)], limit=1)
                if invest:
                    exit.investment_id = invest.name
                    exit.investment_percentage = invest.percentage
                else:
                    exit.investment_id = False
                    exit.investment_percentage = 0.0
            else:
                exit.investment_id = False
                exit.investment_percentage = 0.0

    # ============================ Constrains Methods ============================
    @api.constrains('exit_percentage', 'investment_percentage')
    def _check_exit_percentage(self):
        for line in self:
            if line.exit_percentage <= 0:
                raise ValidationError(_('Exit percentage must be positive.'))
            if line.exit_percentage > line.investment_percentage:
                raise ValidationError(_('Exit percentage cannot exceed current investment percentage (%.2f%%).')
                                    % line.investment_percentage)

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

    @api.constrains('partner_id', 'exit_id.property_id')
    def _check_partner_id(self):
        for line in self:
            invest = line.partner_id.investment_ids.search([('name', '=', line.investment_id)])
            if not invest:
                raise ValidationError(_('The partner has no investment with the name: %s') % line.investment_id)
            if invest.status != 'confirmed':
                raise ValidationError(_('The investment must be confirmed.'))

    # ============================ Validation Functions ============================
    def validate_exiting_partner_status_investment(self):
        if self.partner_id.status != 'active' or self.partner_id.active == False:
            raise ValidationError(_('The old partner (%s) is not active .', self.partner_id.name))

        invest = self.partner_id.investment_ids.search([('name', '=', self.investment_id)])
        if not invest:
            raise ValidationError(
                _('The old partner (%s) has no investment in this property.', self.partner_id.name))

        check_full =  self.exit_type == 'full' and (invest.percentage != self.investment_percentage or invest.status != 'withdrawn')
        check_partial = self.exit_type == 'partial' and (
                invest.percentage != self.investment_percentage - self.exit_percentage or invest.status != 'confirmed')

        if check_full or check_partial:
            raise ValidationError(
                _('The investment of old partner (%s) is not equal to the exit percentage .', self.partner_id.name))