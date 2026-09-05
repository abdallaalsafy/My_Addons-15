# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RealEstateExpenseCategory(models.Model):
    _name = 'real.estate.expense.category'
    _description = 'Real Estate Expense Category'
    _order = 'name asc'

    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Char(string='Category Code', required=True, copy=False)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color Index', default=0)
    
    expense_ids = fields.One2many('real.estate.expense', 'category_id', string='Expenses')
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count', store=True)
    
    active = fields.Boolean(string='Active', default=True)

    @api.depends('expense_ids')
    def _compute_expense_count(self):
        for category in self:
            category.expense_count = len(category.expense_ids)

    @api.constrains('code')
    def _check_unique_code(self):
        for category in self:
            if category.code:
                existing = self.search([('code', '=', category.code), ('id', '!=', category.id)])
                if existing:
                    raise ValidationError(_('Category code must be unique. A category with this code already exists.'))

    @api.constrains('name')
    def _check_unique_name(self):
        for category in self:
            if category.name:
                existing = self.search([('name', '=ilike', category.name), ('id', '!=', category.id)])
                if existing:
                    raise ValidationError(_('Category name must be unique. A category with this name already exists.'))