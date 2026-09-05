# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CompanyFinancialSummary(models.TransientModel):
    _name = 'company.financial.summary'
    _description = 'Company Financial Summary'
    _transient = True

    # Computed Fields
    total_company_balance = fields.Float(string='Total Company Balance', compute='_compute_financial_summary', store=True)
    actual_liquidity = fields.Float(string='Actual Liquidity', compute='_compute_financial_summary', store=True)
    
    # Detailed Breakdown
    management_fees = fields.Float(string='Management Fees', compute='_compute_financial_summary', store=True)
    property_assets = fields.Float(string='Property Assets', compute='_compute_financial_summary', store=True)
    sold_child_property_assets = fields.Float(string='Sold Child Property Assets', compute='_compute_financial_summary', store=True)

    # Transaction Breakdown
    positive_transactions = fields.Float(string='Positive Transactions', compute='_compute_financial_summary', store=True)
    negative_transactions = fields.Float(string='Negative Transactions', compute='_compute_financial_summary', store=True)

    expense_paid = fields.Float(string='Expense Paid', compute='_compute_financial_summary', store=True)

    # Payment Breakdown
    purchase_paid = fields.Float(string='Purchase Paid', compute='_compute_financial_summary', store=True)
    sale_paid = fields.Float(string='Sale Paid', compute='_compute_financial_summary', store=True)
    property_expenses_paid = fields.Float(string='Property Expenses Paid', compute='_compute_financial_summary', store=True)
    undistributed_company_expenses = fields.Float(string='Undistributed Company Expenses', compute='_compute_financial_summary', store=True)
    
    # Partners Statistics
    partners_count = fields.Integer(string='Partners Count', compute='_compute_financial_summary', store=True)
    partners_total_investments = fields.Float(string='Partners Total Investments', compute='_compute_financial_summary', store=True)
    partners_actual_balance = fields.Float(string='Partners Actual Balance', compute='_compute_financial_summary',store=True)
    partners_current_balance = fields.Float(string='Partners Current Balance', compute='_compute_financial_summary',
                                           store=True)
    partners_negative_actual_balance_total = fields.Float(string='Partners Negative Actual Balance Total', compute='_compute_financial_summary', store=True)
    partners_negative_actual_balance_count = fields.Integer(string='Partners with Negative Actual Balance', compute='_compute_financial_summary', store=True)
    partners_exited_count = fields.Integer(string='Partners Exited Count', compute='_compute_financial_summary', store=True)

    # Properties Statistics
    properties_total_cost = fields.Float(string='Properties Total Cost', compute='_compute_financial_summary', store=True)
    properties_sold_count = fields.Integer(string='Sold Properties Count', compute='_compute_financial_summary', store=True)
    properties_active_count = fields.Integer(string='Active Properties Count', compute='_compute_financial_summary', store=True)
    properties_parent_count = fields.Integer(string='Parent Properties Count', compute='_compute_financial_summary', store=True)
    
    # Sales Statistics
    sales_count = fields.Integer(string='Sales Count', compute='_compute_financial_summary', store=True)
    sales_total_price = fields.Float(string='Sales Total Price', compute='_compute_financial_summary', store=True)
    sales_total_profit = fields.Float(string='Sales Total Profit', compute='_compute_financial_summary', store=True)
    sales_total_management_fees = fields.Float(string='Sales Total Management Fees', compute='_compute_financial_summary', store=True)
    sales_paid_count = fields.Integer(string='Sales Paid Count', compute='_compute_financial_summary', store=True)
    sales_unpaid_count = fields.Integer(string='Sales Unpaid Count', compute='_compute_financial_summary', store=True)
    sales_remaining_balance = fields.Float(string='Sales Remaining Balance', compute='_compute_financial_summary', store=True)
    
    # Expenses Statistics
    expenses_count = fields.Integer(string='Expenses Count', compute='_compute_financial_summary', store=True)
    expenses_total_amount = fields.Float(string='Expenses Total Amount', compute='_compute_financial_summary', store=True)
    expenses_investment_count = fields.Integer(string='Investment Expenses Count', compute='_compute_financial_summary', store=True)
    expenses_investment_amount = fields.Float(string='Investment Expenses Amount', compute='_compute_financial_summary', store=True)
    expenses_company_count = fields.Integer(string='Company Expenses Count', compute='_compute_financial_summary', store=True)
    expenses_company_amount = fields.Float(string='Company Expenses Amount', compute='_compute_financial_summary', store=True)
    
    # Expenses Payment Status
    expenses_investment_paid_count = fields.Integer(string='Investment Expenses Paid Count', compute='_compute_financial_summary', store=True)
    expenses_investment_paid_amount = fields.Float(string='Investment Expenses Paid Amount', compute='_compute_financial_summary', store=True)
    expenses_investment_unpaid_count = fields.Integer(string='Investment Expenses Unpaid Count', compute='_compute_financial_summary', store=True)
    expenses_investment_unpaid_amount = fields.Float(string='Investment Expenses Unpaid Amount', compute='_compute_financial_summary', store=True)
    expenses_company_paid_count = fields.Integer(string='Company Expenses Paid Count', compute='_compute_financial_summary', store=True)
    expenses_company_paid_amount = fields.Float(string='Company Expenses Paid Amount', compute='_compute_financial_summary', store=True)
    expenses_company_unpaid_count = fields.Integer(string='Company Expenses Unpaid Count', compute='_compute_financial_summary', store=True)
    expenses_company_unpaid_amount = fields.Float(string='Company Expenses Unpaid Amount', compute='_compute_financial_summary', store=True)
    expenses_paid_count = fields.Integer(string='Expenses Paid Count', compute='_compute_financial_summary', store=True)
    expenses_unpaid_count = fields.Integer(string='Expenses Unpaid Count', compute='_compute_financial_summary', store=True)
    expenses_unpaid_amount = fields.Float(string='Expenses Unpaid Amount', compute='_compute_financial_summary', store=True)
    
    # Expenses Distribution Status
    expenses_undistributed_count = fields.Integer(string='Undistributed Expenses Count', compute='_compute_financial_summary', store=True)
    expenses_undistributed_amount = fields.Float(string='Undistributed Expenses Amount', compute='_compute_financial_summary', store=True)
    expenses_distributed_count = fields.Integer(string='Distributed Expenses Count', compute='_compute_financial_summary', store=True)
    expenses_distributed_amount = fields.Float(string='Distributed Expenses Amount', compute='_compute_financial_summary', store=True)
    
    # Date Filter
    date_from = fields.Date(string='Date From', default=fields.Date.today)

    @api.depends('date_from')
    def _compute_financial_summary(self):
        """Compute all financial summary fields"""
        for record in self:
            # Get all relevant records
            partners = self.env['real.estate.partner'].search([('status', '=', 'active')])
            properties = self.env['real.estate.property'].search([])
            expenses = self.env['real.estate.expense'].search([])
            sales = self.env['real.estate.property.sale'].search([])
            exits = self.env['real.estate.partner.exit'].search([])
            
            # 1. Partners Positive Actual Balance (Sum of all positive actual balances)
            # Because negative balances are not partner money, its expensive money on him
            record.partners_actual_balance = sum(
                partner.actual_balance
                for partner in partners
                if partner.actual_balance > 0
            )
            
            # 2. Management Fees
            record.management_fees = sum(
                sale.management_fee_amount for sale in sales
            ) + sum(
                exit.management_fee_amount for exit in exits
            )

            # 3_0. ChildProperty Assets (total_cost)
            record.sold_child_property_assets = sum(
                property.total_cost
                for property in properties
                if property.status == 'sold' and property.is_child and property.parent_id.status != 'sold'
            )
            # 3. Property Assets (total_cost)
            record.property_assets = sum(
                property.total_cost 
                for property in properties 
                if property.status != 'sold' and property.is_child == False
            )
            
            # 4. Positive Transactions
            record.positive_transactions = sum(
                t.amount 
                for partner in partners 
                for t in partner.transaction_ids 
                if t.transaction_type in ['deposit', 'profit_distribution', 'investment_return']
            )
            
            # 5. Negative Transactions
            record.negative_transactions = sum(
                t.amount 
                for partner in partners 
                for t in partner.transaction_ids 
                if t.transaction_type in ['withdrawal', 'expense']
            )

            # 6.0 Paid Expense
            record.expense_paid = sum(
                expense.amount
                for expense in expenses
                if expense.status == 'paid'
            )
            
            # 7. Undistributed Company Expenses
            record.undistributed_company_expenses = sum(
                expense.amount 
                for expense in expenses 
                if expense.expense_type == 'company' and not expense.distribution_ids
            )
            
            # 8. Purchase Paid
            record.purchase_paid = sum(
                sum(p.amount for p in property.purchase_payment_ids if p.status == 'paid')
                for property in properties
            )

            # 9. Sale Paid
            record.sale_paid = sum(
                sum(p.amount for p in property.sale_payment_ids if p.status == 'paid')
                for property in properties if property.status == 'sold'
            )
            
            # 10. Property Expenses Paid
            record.property_expenses_paid = sum(
                exp.amount 
                for exp in expenses 
                if exp.expense_type == 'investment' and exp.status == 'paid'
            )
            
            # 11. Total Company Balance
            record.total_company_balance = record.partners_actual_balance + record.management_fees + record.property_assets - record.sold_child_property_assets - record.undistributed_company_expenses
            
            # 12. Actual Liquidity
            record.actual_liquidity = (
                record.positive_transactions 
                - record.negative_transactions 
                - record.expense_paid
                - record.purchase_paid
                + record.sale_paid
            )
            
            # Partners Statistics
            record.partners_count = len(partners)
            record.partners_total_investments = sum(
                partner.confirmed_investments_total 
                for partner in partners
            )
            record.partners_current_balance = sum(
                partner.current_balance
                for partner in partners
                if partner.current_balance > 0
            )
            record.partners_negative_actual_balance_total = abs(sum(
                partner.actual_balance
                for partner in partners 
                if partner.actual_balance < 0
            ))
            record.partners_negative_actual_balance_count = len(
                [partner for partner in partners if partner.actual_balance < 0]
            )
            record.partners_exited_count = len(
                self.env['real.estate.partner'].search([('status', '=', 'exited')])
            )
            
            # Properties Statistics
            record.properties_parent_count = len(
                properties.filtered(lambda p: not p.is_child)
            )
            record.properties_total_cost = sum(
                property.total_cost
                for property in properties
                if not property.is_child
            )
            record.properties_sold_count = len(
                properties.filtered(lambda p: p.status == 'sold' and not p.is_child)
            )
            record.properties_active_count = len(
                properties.filtered(lambda p: p.status != 'sold' and not p.is_child)
            )
            
            # Sales Statistics
            record.sales_count = len(sales)
            record.sales_total_price = sum(
                sale.sale_price for sale in sales
            )
            record.sales_total_profit = sum(
                sale.total_profit for sale in sales
            )
            record.sales_total_management_fees = sum(
                sale.management_fee_amount for sale in sales
            )
            record.sales_paid_count = len(
                sales.filtered(lambda s: s.remaining_balance <= 0)
            )
            record.sales_unpaid_count = len(
                sales.filtered(lambda s: s.remaining_balance > 0)
            )
            record.sales_remaining_balance = sum(
                sale.remaining_balance for sale in sales
                if sale.remaining_balance > 0
            )
            
            # Expenses Statistics
            record.expenses_count = len(expenses)
            record.expenses_total_amount = sum(
                expense.amount for expense in expenses
            )
            record.expenses_investment_count = len(
                expenses.filtered(lambda e: e.expense_type == 'investment')
            )
            record.expenses_investment_amount = sum(
                expense.amount for expense in expenses if expense.expense_type == 'investment'
            )
            record.expenses_company_count = len(
                expenses.filtered(lambda e: e.expense_type == 'company')
            )
            record.expenses_company_amount = sum(
                expense.amount for expense in expenses if expense.expense_type == 'company'
            )
            
            # Expenses Payment Status
            investment_expenses = expenses.filtered(lambda e: e.expense_type == 'investment')
            company_expenses = expenses.filtered(lambda e: e.expense_type == 'company')
            
            record.expenses_investment_paid_count = len(
                investment_expenses.filtered(lambda e: e.status == 'paid')
            )
            record.expenses_investment_paid_amount = sum(
                e.amount for e in investment_expenses if e.status == 'paid'
            )
            record.expenses_investment_unpaid_count = len(
                investment_expenses.filtered(lambda e: e.status != 'paid')
            )
            record.expenses_investment_unpaid_amount = sum(
                e.amount for e in investment_expenses if e.status != 'paid'
            )
            
            record.expenses_company_paid_count = len(
                company_expenses.filtered(lambda e: e.status == 'paid')
            )
            record.expenses_company_paid_amount = sum(
                e.amount for e in company_expenses if e.status == 'paid'
            )
            record.expenses_company_unpaid_count = len(
                company_expenses.filtered(lambda e: e.status != 'paid')
            )
            record.expenses_company_unpaid_amount = sum(
                e.amount for e in company_expenses if e.status != 'paid'
            )
            
            record.expenses_paid_count = len(
                expenses.filtered(lambda e: e.status == 'paid')
            )
            record.expenses_unpaid_count = len(
                expenses.filtered(lambda e: e.status != 'paid')
            )
            record.expenses_unpaid_amount = sum(
                e.amount for e in expenses if e.status != 'paid'
            )
            
            # Expenses Distribution Status
            record.expenses_undistributed_count = len(
                expenses.filtered(lambda e: not e.distribution_ids)
            )
            record.expenses_undistributed_amount = sum(
                e.amount for e in expenses if not e.distribution_ids
            )
            record.expenses_distributed_count = len(
                expenses.filtered(lambda e: e.distribution_ids)
            )
            record.expenses_distributed_amount = sum(
                e.amount for e in expenses if e.distribution_ids
            )

    def action_print_report(self):
        """Print the financial summary report"""
        return self.env.ref('real_estate_partnership_management.action_report_company_financial_summary').report_action(self)
