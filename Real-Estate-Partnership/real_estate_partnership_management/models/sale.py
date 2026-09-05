# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from random import randint

# Sale Model
class RealEstatePropertySale(models.Model):
    _name = 'real.estate.property.sale'
    _description = 'Real Estate Property Sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sale_date desc'


    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Sale Reference', required=True, copy=False, default=lambda self: _('New'))
    color = fields.Integer(string='Color', default=_get_default_color)
    # Relations
    property_id = fields.Many2one('real.estate.property', string='Property', required=True, tracking=True, index=True,
                                  domain=lambda self: self.env['real.estate.property'].get_available_for_sale_properties_domain(),ondelete='cascade')
    buyer_contact_id = fields.Many2one('real.estate.contact', string='Buyer Contact', tracking=True, required=True, index=True, ondelete='restrict',)
    # Sale Details
    sale_date = fields.Date(string='Sale Date', required=True, default=fields.Date.today, tracking=True)
    sale_price = fields.Float(string='Sale Price', required=True, tracking=True)
    down_payment = fields.Float(string='Down Payment', tracking=True, help='Down payment amount for the property sale')
    remaining_balance = fields.Float(string='Remaining Balance', compute='_compute_remaining_balance', store=True, tracking=True)
    # Financial Calculations
    total_cost = fields.Float(related='property_id.total_cost', string='Total Cost', store=True)
    total_profit = fields.Float(string='Total Profit', compute='_compute_financials', store=True)
    net_profit = fields.Float(string='Net Profit', compute='_compute_financials', store=True)
    management_fee_percentage = fields.Float(string='Management Fee %', default=5.0, tracking=True)
    management_fee_amount = fields.Float(string='Management Fee Amount', compute='_compute_financials', store=True)
    # Payment Information
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('installment', 'Installment'),
    ], string='Payment Method', default='cash', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', tracking=True)
    
    # Notes and Documents
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    # Related Data
    sale_line_ids = fields.One2many('real.estate.property.sale.line', 'sale_id', string='Sale Lines')
    payment_installment_ids = fields.One2many('real.estate.payment.installment', 'sale_id', string='Payment Installments')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.property.sale') or _('New')
        
        sales = super(RealEstatePropertySale, self).create(vals_list)
        
        # Execute action_confirm_sale for each created sale
        for sale in sales:
            # Create down payment installment if down_payment is specified
            if sale.down_payment > 0:
                sale._create_down_payment_installment()

            sale.action_confirm_sale()
        
        return sales

    def write(self, vals):
        # Validate property and partners for sale
        sale_affecting_fields = ['sale_price', 'management_fee_percentage', 'property_id']
        if any(field in vals for field in sale_affecting_fields):
            for sale in self:
                sale.validate_partner_for_sale()
                if 'property_id' in vals and vals['property_id'] != sale.property_id.id:
                    sale.reset_property_status_and_investments()
                    sale.payment_installment_ids.write({'property_id': vals['property_id']})

        result = super(RealEstatePropertySale, self).write(vals)

        # Handle down payment installment updates
        if 'down_payment' in vals:
            for sale in self:
                if sale.down_payment > 0:
                    sale._update_down_payment_installment()
                else:
                    sale._delete_down_payment_installment()

        if any(field in vals for field in sale_affecting_fields):
            for sale in self:
                sale.action_confirm_sale()

        return result

    def unlink(self):
        for sale in self:
            sale.validate_partner_for_sale()
            sale.reset_property_status_and_investments()

            # Because Partner need sale_line_ids in compute Field
            # Because this line compute field cannot be computedS
            sale.sale_line_ids.unlink()
            sale.payment_installment_ids.unlink()
        return super(RealEstatePropertySale, self).unlink()

    # =========================== Compute Functions ===========================

    @api.depends('sale_price','down_payment', 'payment_installment_ids.amount', 'payment_installment_ids.status')
    def _compute_remaining_balance(self):
        for sale in self:
            if not sale._origin.id:
                sale.remaining_balance = sale.sale_price - sale.down_payment
            else:
                # Add paid installments
                paid_installments = sale.payment_installment_ids.filtered(lambda inv: inv.status == 'paid')
                paid_amount = sum(paid_installments.mapped('amount'))
                sale.remaining_balance = sale.sale_price - paid_amount

    @api.depends('total_cost', 'sale_price', 'management_fee_percentage')
    def _compute_financials(self):
        for sale in self:
            if sale.property_id:
                sale.total_profit = sale.sale_price - sale.total_cost
                sale.management_fee_amount = (sale.total_profit * sale.management_fee_percentage) / 100
                sale.net_profit = sale.total_profit - sale.management_fee_amount
            else:
                sale.total_profit = 0.0
                sale.management_fee_amount = 0.0
                sale.net_profit = 0.0

    # =========================== Constraints Functions ===========================

    @api.constrains('sale_price', 'down_payment')
    def _check_sale_price(self):
        for sale in self:
            if sale.sale_price <= 0:
                raise ValidationError(_('Sale price must be positive.'))
            if sale.down_payment < 0:
                raise ValidationError(_('Down payment cannot be negative.'))
            if sale.down_payment > sale.sale_price:
                raise ValidationError(_('Down payment cannot exceed sale price.'))

    @api.constrains('management_fee_percentage')
    def _check_management_fee(self):
        for sale in self:
            if not (0 <= sale.management_fee_percentage <= 100):
                raise ValidationError(_('Management fee percentage must be between 0 and 100.'))

    @api.constrains('sale_date')
    def _check_sale_date(self):
        for sale in self:
            if sale.sale_date and sale.sale_date > fields.Date.today():
                raise ValidationError(_('Sale date cannot be in the future.'))

    @api.constrains('sale_date', 'property_id')
    def _check_sale_date_vs_purchase_date(self):
        """
        Ensure sale date is not earlier than property purchase date and
        Ensure sale date is not earlier than investment dates
        """
        for sale in self:
            parent_property = sale.property_id if not sale.property_id.is_child else sale.property_id.parent_id
            if sale.sale_date and parent_property:
                if sale.sale_date < parent_property.purchase_date:
                    raise ValidationError(_('Sale date cannot be earlier than property purchase date. '
                                            'Purchase date: %s, Sale date: %s') %
                                          (parent_property.purchase_date, sale.sale_date))
                # Ensure sale date is not earlier than investment dates
                for investment in parent_property.investment_ids.filtered(lambda inv: inv.status == 'confirmed'):
                    if investment.investment_date and sale.sale_date < investment.investment_date:
                        raise ValidationError(_('Sale date cannot be earlier than investment date. '
                                                'Investment: %s, Investment date: %s, Sale date: %s') %
                                              (investment.name, investment.investment_date, sale.sale_date))

    @api.constrains('property_id')
    def _check_property_sale_eligibility(self):
        for sale in self:
            if sale.property_id:
                # Check if property is already sold
                if sale.property_id.status == 'sold':
                    raise ValidationError(_('This property is already sold and cannot be sold again.'))

                # Check if property is either a child or a parent with no children
                if sale.property_id.has_any_children:
                    raise ValidationError(
                        _('Cannot sell a parent property that has child properties. Sell the child properties instead.'))

                # Validate property for sale
                sale.property_id.validate_confirmed_investment_percentage_and_total_amount()

    # =========================== Validation Functions ===========================

    def reset_property_status_and_investments(self):
        # Update old property status and its parent
        parent_property = self.property_id.parent_id if self.property_id.is_child else self.property_id
        parent_property.write({'status': 'available','sale_id': False,})
        self.property_id.write({'status': 'available','sale_id': False,})

        # Get confirmed investments
        distributed_investments = parent_property.investment_ids.filtered(lambda inv: inv.status == 'distributed')
        distributed_investments.write({'status': 'confirmed'})

    def validate_partner_for_sale(self):
        partners = self.sale_line_ids.mapped(lambda x: x.partner_id)
        for partner in partners:
            if partner.status != 'active' or not partner.active:
                raise ValidationError(_('Cannot create distribute sale: partner "%s" is not active.') % partner.name)

    def _check_partner_balance_restriction(self):
        """Check if sale should be restricted due to low partner balances"""
        self.ensure_one()

        # Get the setting value
        restrict_sale = self.env.company.restrict_sale_on_low_balance

        if not restrict_sale:
            return

        # Get the parent property for investments
        parent_property = self.property_id.parent_id if self.property_id.is_child else self.property_id

        # Get confirmed investments
        confirmed_investments = parent_property.investment_ids.filtered(lambda inv: inv.status == 'confirmed')

        # Check each partner's balance against their investment
        for investment in confirmed_investments:
            partner = investment.partner_id
            if partner.current_balance < investment.amount:
                raise ValidationError(
                    _('Cannot sell property "%s". Partner "%s" has balance %.2f which is less than their investment amount %.2f. '
                      'Please ensure all partners have sufficient balance before selling.') %
                    (self.property_id.name, partner.name, partner.current_balance, investment.amount)
                )

    # =========================== Action Functions ===========================
    def action_confirm_sale(self):
        """Confirm the property sale"""
        self.ensure_one()

        vals_list = []

        # Get the parent property for investments (always use parent for investments)
        parent_property = self.property_id.parent_id if self.property_id.is_child else self.property_id

        # Get confirmed investments
        confirmed_investments = parent_property.investment_ids.filtered(lambda inv: inv.status == 'confirmed')

        # Check partner balance restriction if enabled
        self._check_partner_balance_restriction()

        # Create sale lines for each investor
        for investment in confirmed_investments:
            partner_profit_share = (self.net_profit * investment.percentage) / 100
            vals_list.append({
                'sale_id': self.id,
                'partner_id': investment.partner_id.id,
                'investment_id': investment.id,
                'investment_amount': investment.amount,
                'investment_percentage': investment.percentage,
                'profit_amount': partner_profit_share,
            })

        self.sale_line_ids.unlink()
        # Create exit lines for all partners
        self.env['real.estate.property.sale.line'].create(vals_list)

        # Update property status
        self.property_id.write({
            'status': 'sold',
            'sale_id': self.id,
        })

        # Update investment status
        if not self.property_id.is_child:
            confirmed_investments.write({'status': 'distributed'})

    def _create_down_payment_installment(self):
        """Create a down payment installment for this sale"""
        installment_vals = {
            'property_id': self.property_id.id,
            'contact_id': self.buyer_contact_id.id,
            'payment_type': 'sale',
            'amount': self.down_payment,
            'due_date': self.sale_date,
            'status': 'paid',
            'is_down_payment': True,
            'payment_method': 'cash',  # Default payment method
            'payment_reference': f'Down payment for sale {self.name}',
        }

        self.env['real.estate.payment.installment'].create(installment_vals)

    def _update_down_payment_installment(self):
        """Update the down payment installment amount"""
        down_payment_installment = self.payment_installment_ids.filtered(lambda p: p.is_down_payment)
        if down_payment_installment:
            down_payment_installment[0].with_context(update_from_sale_code=True).write({'amount': self.down_payment})
        else:
            # If no down payment installment exists, create one
            self._create_down_payment_installment()

    def _delete_down_payment_installment(self):
        """Delete the down payment installment"""
        down_payment_installment = self.payment_installment_ids.filtered(lambda p: p.is_down_payment)
        if down_payment_installment:
            down_payment_installment.unlink()

    def action_generate_sale_payment_receipts(self):
        """Open wizard to generate multiple sale payment receipts"""
        self.ensure_one()
        
        # Validate sale can accept new sale payment
        self.env['real.estate.payment.installment'].validate_property_for_sale_payment(self.property_id)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Sale Payment Receipts'),
            'res_model': 'purchase.payment.receipts.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.property_id.id,
                'default_sale_id': self.id,
            },
        }

