# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstatePartnerExit(models.Model):
    _name = 'real.estate.partner.exit'
    _description = 'Real Estate Partner Exit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'exit_date desc'

    name = fields.Char(string='Exit Reference', required=True, copy=False, default=lambda self: _('New'))
    
    # Relations
    property_id = fields.Many2one('real.estate.property', string='Property', required=True, tracking=True, ondelete='cascade',
                                  domain=lambda self: self.env['real.estate.property'].get_exit_properties_domain())
    # Exit Details
    exit_date = fields.Date(string='Exit Date', required=True, default=fields.Date.today, tracking=True)
    current_property_value = fields.Float(string='Current Property Value', required=True, tracking=True)
    total_property_cost = fields.Float(string='Total Property Cost', required=True, readonly=True, tracking=True)
    
    actual_property_profit = fields.Float(string='Actual Property Profit', compute='_compute_actual_property_profit',
                                          store=True)
    management_fee_percentage = fields.Float(string='Management Fee %', default=5.0, tracking=True)
    management_fee_amount = fields.Float(string='Management Fee Amount', compute='_compute_financials', store=True)
    net_profit = fields.Float(string='Net Profit', compute='_compute_financials', store=True)

    # Notes
    notes = fields.Text(string='Notes')
    
    # Exiting Partners Lines
    exiting_partner_ids = fields.One2many('real.estate.partner.exit.exiting', 'exit_id', string='Exiting Partners',)
    # Replacement Partners Lines
    replacement_partner_ids = fields.One2many('real.estate.partner.exit.replacement', 'exit_id', string='Replacement Partners')
    # Exit Lines (for profit distribution to all partners)
    exit_line_ids = fields.One2many('real.estate.partner.exit.lines', 'exit_id', string='Exit Lines')
    
    # Computed fields
    total_exit_percentage = fields.Float(string='Total Exit Percentage', compute='_compute_total_exit_percentage', store=True)
    total_replacement_percentage = fields.Float(string='Total Replacement Percentage', compute='_compute_total_replacement_percentage', store=True)

    # =========================== Built-in Functions ===========================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.partner.exit') or _('New')
        
        res = super(RealEstatePartnerExit, self).create(vals_list)

        for record in res:
            record.action_approve_exit()
        return res

    # Prevent modification after approval or when distribution lines exist
    def write(self, vals):
        exit_affecting_fields = ['property_id', 'exiting_partner_ids','replacement_partner_ids']
        if any(field in vals for field in exit_affecting_fields):
            raise ValidationError(_("You cannot modify this exit , delete existing and then create new."))

        rtn = super(RealEstatePartnerExit, self).write(vals)

        exit_allow_fields = ['current_property_value', 'management_fee_percentage']
        if any(field in vals for field in exit_allow_fields):
            for exit in self:
                exit.check_is_last_exit()

                if exit.property_id.status == 'sold':
                    raise ValidationError(_("Property %s is already sold.") % exit.property_id.name)

                exit.update_exit_lines_and_validate_partner_status()

        return rtn

    # Prevent deletion after approval or after a grace period
    def unlink(self):
        for exit in self:
            exit.check_is_last_exit()
            exit.check_exit_replacement_status_and_investments()
            exit.action_reset_exit_and_replacement_investments()

            # Because Partner need exit_line_ids in compute Field
            # Because this line compute field cannot be computedS
            exit.exit_line_ids.unlink()
        return super(RealEstatePartnerExit, self).unlink()

    # =========================== Onchange Functions ===========================
    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.total_property_cost = self.property_id.total_cost
            self.current_property_value = self.property_id.current_value

    # =========================== Compute Functions ===========================

    @api.depends('current_property_value', 'total_property_cost')
    def _compute_actual_property_profit(self):
        for exit in self:
            exit.actual_property_profit = exit.current_property_value - exit.total_property_cost

    @api.depends('actual_property_profit', 'management_fee_percentage')
    def _compute_financials(self):
        for exit in self:
            exit.management_fee_amount = (exit.actual_property_profit * exit.management_fee_percentage) / 100
            exit.net_profit = exit.actual_property_profit - exit.management_fee_amount

    @api.depends('exiting_partner_ids.exit_percentage')
    def _compute_total_exit_percentage(self):
        for exit in self:
            exit.total_exit_percentage = sum(line.exit_percentage for line in exit.exiting_partner_ids)

    @api.depends('replacement_partner_ids.replacement_percentage')
    def _compute_total_replacement_percentage(self):
        for exit in self:
            exit.total_replacement_percentage = sum(line.replacement_percentage for line in exit.replacement_partner_ids)

    # =========================== Constraints Functions ===========================
    @api.constrains('current_property_value', 'total_property_cost')
    def _check_amounts(self):
        for exit in self:
            if exit.current_property_value <= 0:
                raise ValidationError(_('Current property value must be positive.'))
            if exit.total_property_cost <= 0:
                raise ValidationError(_('Total property cost must be positive.'))

    @api.constrains('management_fee_percentage')
    def _check_management_fee(self):
        for exit in self:
            if not (0 <= exit.management_fee_percentage <= 100):
                raise ValidationError(_('Management fee percentage must be between 0 and 100.'))

    @api.constrains('exit_date')
    def _check_exit_date(self):
        for exit in self:
            if exit.exit_date > fields.Date.today():
                raise ValidationError(_('Exit date cannot be in the future.'))

    @api.constrains('exit_date', 'property_id')
    def _check_exit_date_vs_purchase_date(self):
        """Ensure exit date is not earlier than property purchase date"""
        for exit in self:
            if exit.exit_date and exit.property_id and exit.property_id.purchase_date:
                if exit.exit_date < exit.property_id.purchase_date:
                    raise ValidationError(_('Exit date cannot be earlier than property purchase date. '
                                          'Purchase date: %s, Exit date: %s') % 
                                        (exit.property_id.purchase_date, exit.exit_date))

    @api.constrains('exit_date', 'exiting_partner_ids')
    def _check_exit_date_vs_investment_date(self):
        """Ensure exit date is not earlier than investment dates"""
        for exit in self:
            if exit.exit_date and exit.exiting_partner_ids:
                for exiting_partner in exit.exiting_partner_ids:
                    invest = exiting_partner.partner_id.investment_ids.search([('name', '=', exiting_partner.investment_id)])
                    if exiting_partner.investment_id and invest.investment_date:
                        if exit.exit_date < invest.investment_date:
                            raise ValidationError(_('Exit date cannot be earlier than investment date. '
                                                  'Investment date: %s, Exit date: %s') % 
                                                (invest.investment_date, exit.exit_date))
                    # Ensure exit date is not earlier than partner join dates
                    if exiting_partner.partner_id and exiting_partner.partner_id.join_date:
                        if exit.exit_date < exiting_partner.partner_id.join_date:
                            raise ValidationError(_('Exit date cannot be earlier than partner join date. '
                                                  'Join date: %s, Exit date: %s') %
                                                (exiting_partner.partner_id.join_date, exit.exit_date))

    @api.constrains('total_exit_percentage', 'total_replacement_percentage')
    def _check_exit_replacement_percentage(self):
        for exit in self:
            if exit.total_exit_percentage != exit.total_replacement_percentage:
                raise ValidationError(_('Total exit percentage (%.2f%%) must equal total replacement percentage (%.2f%%).')
                                    % (exit.total_exit_percentage, exit.total_replacement_percentage))

    @api.constrains('exiting_partner_ids', 'replacement_partner_ids')
    def _check_exit_replacement_duplicate(self):
        for exit in self:
            # Check for duplicate partners
            exiting_partners = exit.exiting_partner_ids.mapped('partner_id')
            replacement_partners = exit.replacement_partner_ids.mapped('partner_id')
            duplicate_partners = exiting_partners & replacement_partners
            if duplicate_partners:
                raise ValidationError(
                    _('A partner cannot be both in exiting and replacement partners. Duplicate partners: %s')
                    % ', '.join(duplicate_partners.mapped('name')))

    # =========================== Action Functions ===========================
    def action_approve_exit(self):
        """Execute the partner exit and update investment"""
        self.ensure_one()

        # Validate that there are exiting partners
        if not self.exiting_partner_ids:
            raise ValidationError(_('At least one exiting partner must be specified.'))

        # Validate that there are replacement partners
        if not self.replacement_partner_ids:
            raise ValidationError(_('At least one replacement partner must be specified.'))

        # Validate property for sale
        self.property_id.validate_confirmed_investment_percentage_and_total_amount()

        # Get confirmed investments
        confirmed_investments = self.property_id.investment_ids.filtered(lambda invs: invs.status == 'confirmed')
        # Create exit lines for all partners (profit distribution)
        vals_list = []
        for inv in confirmed_investments:
            # Each partner gets profit based on their current percentage
            partner_profit_share = inv.percentage * self.net_profit / 100
            vals_list.append({
                'exit_id': self.id,
                'partner_id': inv.partner_id.id,
                'investment_percentage': inv.percentage,
                'original_investment_amount': inv.amount,
                'profit_amount': partner_profit_share,
                'is_exiting_partner': inv.partner_id.id in self.exiting_partner_ids.mapped('partner_id.id'),
            })
        self.env['real.estate.partner.exit.lines'].create(vals_list)

        # Process exiting partners - update their investments
        for exiting_line in self.exiting_partner_ids:
            investment = exiting_line.partner_id.investment_ids.search([('name', '=', exiting_line.investment_id)])
            if exiting_line.exit_type == 'full':
                # Full exit - mark investment as withdrawn
                investment.write({
                    'status': 'withdrawn',
                    'withdrawal_date': self.exit_date,
                    'withdrawal_ref': f'Partner exit - Ref: {self.name}',
                })
            else:
                # Partial exit - reduce percentage
                new_percentage = investment.percentage - exiting_line.exit_percentage
                investment.write({'input_percentage': new_percentage})

        # Process replacement partners - create or update their investments
        for replacement_line in self.replacement_partner_ids:
            if replacement_line.partner_type == 'new':
                # Create new investment for new partner
                self.env['real.estate.property.investment'].create({
                    'partner_id': replacement_line.partner_id.id,
                    'property_id': self.property_id.id,
                    'input_percentage': replacement_line.replacement_percentage,
                    'investment_date': self.exit_date,
                    'notes': f'Replacement investment for exit - Ref: {self.name}',
                })
            elif replacement_line.partner_type == 'existing':
                # Update existing investment
                existing_investment = replacement_line.partner_id.investment_ids.search([('name', '=', replacement_line.investment_id)])
                new_percentage = existing_investment.percentage + replacement_line.replacement_percentage
                existing_investment.write({'input_percentage': new_percentage})

        # Update property current value
        self.property_id.write({'current_value': self.current_property_value})

    def action_reset_exit_and_replacement_investments(self):
        # Remove or reduce investments for replacement partners
        for replacement_line in self.replacement_partner_ids:
            if replacement_line.partner_type == 'new':
                # Delete the investment that was created for new partner
                new_investment = self.env['real.estate.property.investment'].search([
                    ('partner_id', '=', replacement_line.partner_id.id),
                    ('property_id', '=', self.property_id.id),
                    ('status', '=', 'confirmed')
                ], limit=1)
                new_investment.unlink()
            elif replacement_line.partner_type == 'existing':
                # Reduce the percentage that was added to existing investment
                existing_investment = replacement_line.partner_id.investment_ids.search(
                    [('name', '=', replacement_line.investment_id)])
                if existing_investment:
                    original_percentage = existing_investment.percentage - replacement_line.replacement_percentage
                    existing_investment.write({'input_percentage': original_percentage})

        # Restore investments to their original state for exiting partners
        for exiting_line in self.exiting_partner_ids:
            investment = exiting_line.partner_id.investment_ids.search(
                [('name', '=', exiting_line.investment_id)])
            if investment:
                if exiting_line.exit_type == 'full':
                    # Restore from withdrawn to confirmed
                    investment.write({
                        'status': 'confirmed',
                        'withdrawal_date': False,
                        'withdrawal_ref': False,
                    })
                else:
                    # Restore original percentage
                    original_percentage = investment.percentage + exiting_line.exit_percentage
                    investment.write({'input_percentage': original_percentage})

    def check_is_last_exit(self):
        not_last_exit_for_property = self.search(
            [('property_id', '=', self.property_id.id), ('id', '>', self.id)])
        if not_last_exit_for_property:
            raise ValidationError(_("You cannot delete or update this exit , because there is a later exit."))


    def check_exit_replacement_status_and_investments(self):
        for exiting_partner in self.exiting_partner_ids:
            exiting_partner.validate_exiting_partner_status_investment()

        for replacement_partner in self.replacement_partner_ids:
            replacement_partner.validate_replacement_partner_status_investment()

    def update_exit_lines_and_validate_partner_status(self):
        for exit_line in self.exit_line_ids:
            exit_line.validate_exit_line_partner()
            partner_profit_share = exit_line.investment_percentage * self.net_profit / 100
            exit_line.profit_amount = partner_profit_share


