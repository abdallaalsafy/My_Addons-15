# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RealEstateManagementFeeSummary(models.TransientModel):
    _name = 'real.estate.management.fee.summary'
    _description = 'Real Estate Management Fee Summary'
    _transient = True

    # Common fields
    fee_type = fields.Selection([
        ('sale', 'Sale'),
        ('exit', 'Partner Exit'),
    ], string='Fee Type', readonly=True)
    
    # Reference fields
    reference = fields.Char(string='Reference', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    
    # Property information
    property_id = fields.Many2one('real.estate.property', string='Property', readonly=True)
    property_code = fields.Char(string='Property Code', readonly=True)
    property_name = fields.Char(string='Property Name', readonly=True)
    
    # Financial information
    total_profit = fields.Float(string='Total Profit', readonly=True)
    management_fee_percentage = fields.Float(string='Management Fee %', readonly=True)
    management_fee_amount = fields.Float(string='Management Fee Amount', readonly=True)
    net_profit = fields.Float(string='Net Profit', readonly=True)
    
    # Additional context
    buyer_contact_id = fields.Many2one('real.estate.contact', string='Buyer', readonly=True)
    buyer_name = fields.Char(string='Buyer Name', readonly=True)
    
    # Source record IDs for navigation
    sale_id = fields.Many2one('real.estate.property.sale', string='Sale', readonly=True)
    exit_id = fields.Many2one('real.estate.partner.exit', string='Partner Exit', readonly=True)
    
    @api.model
    def load_management_fees(self):
        """Load management fees from sales and exits"""
        # Clear existing records
        self.search([]).unlink()
        
        # Load from sales
        sales = self.env['real.estate.property.sale'].search([])
        for sale in sales:
            self.create({
                'fee_type': 'sale',
                'reference': sale.name,
                'date': sale.sale_date,
                'property_id': sale.property_id.id,
                'property_code': sale.property_id.code,
                'property_name': sale.property_id.name,
                'total_profit': sale.total_profit,
                'management_fee_percentage': sale.management_fee_percentage,
                'management_fee_amount': sale.management_fee_amount,
                'net_profit': sale.net_profit,
                'buyer_contact_id': sale.buyer_contact_id.id if sale.buyer_contact_id else False,
                'buyer_name': sale.buyer_contact_id.name if sale.buyer_contact_id else '',
                'sale_id': sale.id,
            })
        
        # Load from exits
        exits = self.env['real.estate.partner.exit'].search([])
        for exit in exits:
            self.create({
                'fee_type': 'exit',
                'reference': exit.name,
                'date': exit.exit_date,
                'property_id': exit.property_id.id,
                'property_code': exit.property_id.code,
                'property_name': exit.property_id.name,
                'total_profit': exit.actual_property_profit,
                'management_fee_percentage': exit.management_fee_percentage,
                'management_fee_amount': exit.management_fee_amount,
                'net_profit': exit.net_profit,
                'buyer_contact_id': False,
                'buyer_name': '',
                'exit_id': exit.id,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Management Fees Summary'),
            'res_model': 'real.estate.management.fee.summary',
            'view_mode': 'tree',
            'target': 'current',
        }
