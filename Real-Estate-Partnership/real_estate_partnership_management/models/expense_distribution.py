# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstateExpenseDistribution(models.Model):
    _name = 'real.estate.expense.distribution'
    _description = 'Real Estate Expense Distribution'
    _order = 'expense_id desc, partner_id'

    # Relations
    expense_id = fields.Many2one('real.estate.expense', string='Expense', required=True, index=True, ondelete='cascade')
    partner_id = fields.Many2one('real.estate.partner', string='Partner', required=True, index=True, ondelete='restrict',)
    
    # Distribution Details
    distribution_method = fields.Selection(related='expense_id.distribution_method', string='Distribution Method', readonly=True, store=True)
    partner_share = fields.Float(string='Partner Share', required=True)
    share_percentage = fields.Float(string='Share Percentage', help="Percentage of total expense")
    
    # Calculation Details
    base_amount = fields.Float(related='expense_id.amount', string='Base Expense Amount', readonly=True, store=True)
    calculation_basis = fields.Float(string='Calculation Basis', help="Value used to calculate share (balance or equal share)")
    
    # Status
    status = fields.Selection(related='expense_id.status', string='Status', readonly=True, store=True)

    # Dates
    distribution_date = fields.Date(related='expense_id.expense_date', string='Distribution Date',  readonly=True, store=True)

    # =========================== Constraints Functions ===========================

    @api.constrains('distribution_date', 'partner_id')
    def _check_distribution_date_partner_join_date(self):
        """Ensure distribution date is not earlier than partner join date"""
        for distribution in self:
            if distribution.distribution_date and distribution.partner_id and distribution.partner_id.join_date:
                if distribution.distribution_date < distribution.partner_id.join_date:
                    raise ValidationError(_('Distribution date cannot be earlier than partner join date. '
                                          'Partner join date: %s, Distribution date: %s') %
                                        (distribution.partner_id.join_date, distribution.distribution_date))