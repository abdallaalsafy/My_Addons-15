# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

 
class RealEstatePropertyInvestment(models.Model):
    _name = 'real.estate.property.investment'
    _description = 'Real Estate Property Investment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deal_id,investment_date'


    name = fields.Char(string='Investment Reference', required=True, copy=False, default=lambda self: _('New'))
    investment_date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True, index=True,
                                 domain="[('status', '=', 'active')]",ondelete='restrict')
    deal_id = fields.Many2one('real.estate.deal', string='Deal', required=True, tracking=True, index=True,ondelete='cascade',
                              domain="[('status', '=', 'opening'),'|','&',('total_investments_percentage', '<', 100),('investment_method', '=', 'percentage'),('investment_method', '=', 'amount')]")
    
    # Related fields for easy access
    investment_method = fields.Selection(related='deal_id.investment_method', store=True)
    status = fields.Selection(related='deal_id.status', store=True, index=True)
    total_cost = fields.Float(related='deal_id.total_deal_cost', store=True)

    # Investment Details
    amount = fields.Float(string='Total Amount', compute='_compute_amount', store=True,)
    down_payment = fields.Float(string='Down Payment', compute='_compute_down_payment', store=True, tracking=True, help='Down payment amount for the investment')
    remaining_amount = fields.Float(string='Remaining Amount', compute='_compute_remaining_amount', store=True)
    percentage = fields.Float(string='Percentage %', readonly=True)

    notes = fields.Text(string='Notes')
    # Investment Payment Lines
    payment_line_ids = fields.One2many('real.estate.investment.payment', 'investment_id', string='Payment Installments')

    #=========================== Built-in Functions ===========================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.property.investment') or _('New')
        
        rtn =  super(RealEstatePropertyInvestment, self).create(vals_list)
        return rtn

    def write(self, vals):
        # vals is only allowed to update notes
        all_fields_allowed = set(vals).issubset({'notes'})
        self.validation_update_delete(all_fields_allowed=all_fields_allowed)

        rtn = super(RealEstatePropertyInvestment, self).write(vals)

        return rtn

    def unlink(self):
        self.validation_update_delete()

        ren =  super(RealEstatePropertyInvestment, self).unlink()
        return ren

    def name_get(self):
        result = []
        for investment in self:
            name = f"{investment.name} ({investment.partner_id.name})"
            result.append((investment.id, name))
        return result

    # =========================== Compute Functions ===========================

    @api.depends('percentage', 'deal_id.total_deal_cost')
    def _compute_amount(self):
        for investment in self:
            # Calculate amount from percentage of total cost
            deal_coast = investment.deal_id.total_deal_cost
            investment.amount = (investment.percentage / 100) * deal_coast

    @api.depends('payment_line_ids.amount')
    def _compute_down_payment(self):
        for investment in self:
            investment.down_payment = sum(line.amount for line in investment.payment_line_ids)

    @api.depends('down_payment','amount')
    def _compute_remaining_amount(self):
        for investment in self:
            investment.remaining_amount = investment.amount - investment.down_payment

    # =========================== Constraints Functions ===========================

    @api.constrains('deal_id')
    def _check_deal_id_confirmed_sold_contracts(self):
        for investment in self:
            if investment.deal_id.confirmed_sold_contracts_count > 0:
                raise ValidationError(_('This deal has confirmed sold contracts. Cannot add investment to this deal.'))

    @api.constrains('partner_id', 'deal_id')
    def _check_unique_investment(self):
        for investment in self:
            existing = self.search([
                ('partner_id', '=', investment.partner_id.id),
                ('deal_id', '=', investment.deal_id.id),
                ('id', '!=', investment.id),
            ])
            if existing:
                raise ValidationError(_('Partner already has an investment to this deal.'))

    @api.constrains('investment_date', 'deal_id', 'partner_id')
    def _check_investment_date(self):
        """Ensure investment date is not earlier than property purchase date"""
        for investment in self:
            if investment.investment_date > fields.Date.today():
                raise ValidationError(_('Investment date cannot be in the future.'))
            
            if investment.investment_date < investment.deal_id.open_date:
                raise ValidationError(_('Investment date cannot be earlier than deal open date. '
                                        'deal open date: %s, Investment date: %s') % 
                                    (investment.deal_id.open_date, investment.investment_date))

            if investment.investment_date < investment.partner_id.join_date:
                raise ValidationError(_('Investment date cannot be earlier than partner join date. '
                                        'Join date: %s, Investment date: %s') % 
                                    (investment.partner_id.join_date, investment.investment_date))

# =================================== Logic Functions ===================================

    def validation_update_delete(self,all_fields_allowed=False):
        for investment in self:
            if investment.status != 'opening':
                raise ValidationError(_('Investment is not opening. Cannot update or delete investment.'))
                    
            if investment.deal_id.confirmed_sold_contracts_count > 0 and not all_fields_allowed:
                raise ValidationError(_('This deal has confirmed sold contracts. Cannot update or delete investment to this deal.'))
