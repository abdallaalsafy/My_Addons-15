# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RealEstatePropertyInvestment(models.Model):
    _name = 'real.estate.property.investment'
    _description = 'Real Estate Property Investment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc,investment_date desc'


    name = fields.Char(string='Investment Reference', required=True, copy=False, default=lambda self: _('New'))
    # Relations
    partner_id = fields.Many2one('real.estate.partner', string='Partner', required=True, tracking=True, index=True,
                                 domain="[('status', '=', 'active')]",ondelete='restrict')
    investment_method = fields.Selection(related='property_id.investment_method', string='Investment Method', store=True)
    property_id = fields.Many2one('real.estate.property', string='Property', required=True, tracking=True, index=True,
                                 domain=lambda self: self.env['real.estate.property'].get_investment_properties_domain(),ondelete='cascade')
    total_cost = fields.Float(related='property_id.total_cost', string='Total Cost', store=True)
    # Investment Details
    amount = fields.Float(string='Total Amount', compute='_compute_amount', store=True, tracking=True)
    percentage = fields.Float(string='Percentage %', compute='_compute_percentage', store=True, tracking=True)
    
    # Input fields for flexible investment
    input_percentage = fields.Float(string='Input Percentage %', help='Enter percentage when using percentage-based investment method')

    investment_date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    # Investment Payment Lines
    payment_line_ids = fields.One2many('real.estate.investment.payment', 'investment_id', string='Payment Installments')
    
    # Status
    status = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('distributed', 'Distributed'),
        ('withdrawn', 'Withdrawn'),
    ], string='Status', default='confirmed', tracking=True)
    # Withdrawal Information
    withdrawal_date = fields.Date(string='Withdrawal Date')
    withdrawal_ref = fields.Text(string='Withdrawal Reason')

    # Notes
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.property.investment') or _('New')
        
        return super(RealEstatePropertyInvestment, self).create(vals_list)

    def write(self, vals):
        investment_affecting_fields = ['amount', 'input_percentage', 'property_id', 'partner_id', 'investment_date']
        if any(field in vals for field in investment_affecting_fields):
            for investment in self:
                if investment.status in ['distributed', 'withdrawn']:
                    raise ValidationError(_('Cannot update distributed or withdrawn investments.'))

        return super(RealEstatePropertyInvestment, self).write(vals)

    def unlink(self):
        for investment in self:
            if investment.status in ['distributed','withdrawn']:
                raise ValidationError(_('Cannot delete distributed or withdrawn investments.'))

        return super(RealEstatePropertyInvestment, self).unlink()

    def name_get(self):
        result = []
        for investment in self:
            name = f"{investment.name} ({investment.partner_id.name})"
            result.append((investment.id, name))
        return result

    # =========================== Compute Functions ===========================

    @api.depends('payment_line_ids.amount', 'input_percentage', 'total_cost')
    def _compute_amount(self):
        for investment in self:
            if investment.investment_method == 'percentage':
                # Calculate amount from percentage of total cost
                if investment.total_cost > 0:
                    investment.amount = (investment.input_percentage / 100) * investment.total_cost
                else:
                    investment.amount = 0.0
            else:
                # Use payment lines only (amount-based method not supported anymore)
                if investment.payment_line_ids:
                    amount = sum(line.amount for line in investment.payment_line_ids)
                    investment.amount = amount
                else:
                    investment.amount = 0.0

    @api.depends('amount', 'input_percentage')
    def _compute_percentage(self):
        for investment in self:
            if investment.investment_method == 'percentage':
                # Use input percentage directly
                investment.percentage = investment.input_percentage
            else:
                if investment.property_id.total_investments > 0:
                    investment.percentage = (investment.amount / investment.property_id.total_investments) * 100
                else:
                    investment.percentage = 0.0

    # =========================== Validation Functions ===========================
    
    @staticmethod
    def validate_property_for_investment(property):
        """
        Validate if property can accept new investment
        Raises ValidationError if property cannot accept investment
        """
        if property.is_child:
            raise ValidationError(_('Cannot create investments for child properties. '
                                    'Investments should be made in the parent property only.'))

        if property.status == 'sold':
            raise ValidationError(_('Cannot invest in sold properties.'))

        # Check if property needs new investment (total percentage < 100%)
        # Only check percentage if investment method is 'percentage'
        if property.investment_method == 'percentage':
            confirmed_investments = property.investment_ids.filtered(lambda inv: inv.status == 'confirmed')
            total_percentage = sum(inv.percentage for inv in confirmed_investments)

            if total_percentage > 100:
                raise ValidationError(_('Property investment is already complete (100%%). No new investment needed.'))

    # =========================== Constraints Functions ===========================

    @api.constrains('amount')
    def _check_amount(self):
        for investment in self:
            if investment.amount <= 0:
                raise ValidationError(_('Investment amount must be positive.'))

    @api.constrains('partner_id')
    def _check_partner_active(self):
        """Ensure partner is active for any investment operation"""
        for investment in self:
            if investment.partner_id.status != 'active':
                raise ValidationError(_('Cannot create investments for inactive partners. '
                                      'Partner "%s" is currently %s.') % 
                                    (investment.partner_id.name, investment.partner_id.status))

    @api.constrains('partner_id', 'property_id')
    def _check_unique_investment(self):
        for investment in self:
            existing = self.search([
                ('partner_id', '=', investment.partner_id.id),
                ('property_id', '=', investment.property_id.id),
                ('id', '!=', investment.id),
                ('status', 'in', ['confirmed','distributed']),
            ])
            if existing:
                raise ValidationError(_('Partner already has an investment in this property.'))

    @api.constrains('property_id')
    def _check_property_status(self):
        for investment in self:
            self.validate_property_for_investment(investment.property_id)

    @api.constrains('input_percentage', 'property_id')
    def _check_total_percentage(self):
        """Ensure total investment percentage doesn't exceed 100%"""
        for investment in self:
            if investment.input_percentage and investment.property_id:
                if investment.investment_method == 'percentage':
                    # Calculate total percentage for this property
                    total_percentage = 0.0
                    other_investments = self.search([
                        ('property_id', '=', investment.property_id.id),
                        ('id', '!=', investment.id),
                        ('status', '=', 'confirmed')
                    ])

                    # Add percentages from other investments
                    for other_inv in other_investments:
                        total_percentage += other_inv.percentage

                    # Add current investment percentage
                    total_percentage += investment.input_percentage

                    if total_percentage > 100:
                        raise ValidationError(_('Total investment percentage cannot exceed 100%%. Current total: %.2f%%') % total_percentage)

    @api.constrains('investment_date', 'property_id')
    def _check_investment_date_property_purchase_date(self):
        """Ensure investment date is not earlier than property purchase date"""
        for investment in self:
            if investment.investment_date and investment.property_id and investment.property_id.purchase_date:
                if investment.investment_date < investment.property_id.purchase_date:
                    raise ValidationError(_('Investment date cannot be earlier than property purchase date. '
                                          'Purchase date: %s, Investment date: %s') % 
                                        (investment.property_id.purchase_date, investment.investment_date))

    @api.constrains('investment_date', 'partner_id')
    def _check_investment_date_vs_join_date(self):
        """Ensure investment date is not earlier than partner join date"""
        for investment in self:
            if investment.investment_date and investment.partner_id and investment.partner_id.join_date:
                if investment.investment_date < investment.partner_id.join_date:
                    raise ValidationError(_('Investment date cannot be earlier than partner join date. '
                                          'Join date: %s, Investment date: %s') % 
                                        (investment.partner_id.join_date, investment.investment_date))

    @api.constrains('investment_date')
    def _check_investment_date(self):
        for investment in self:
            if investment.investment_date and investment.investment_date > fields.Date.today():
                raise ValidationError(_('Investment date cannot be in the future.'))

    # =========================== Action Functions ===========================

    def action_request_exit(self):
        """Create partner exit request"""
        if self.status != 'confirmed':
            raise UserError(_('Only confirmed investments can have exit requests.'))

        # Prepare exiting partner line
        exiting_partner_line = {
            'investment_id': self.id,
            'investment_percentage': self.percentage,
            'exit_percentage': self.percentage,
        }

        # Open window with pre-filled data (record will be created when user saves)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Exit Request'),
            'res_model': 'real.estate.partner.exit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.property_id.id,
                'default_exiting_partner_ids': [exiting_partner_line],
            }
        }