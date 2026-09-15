# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CompanyFinancialSummary(models.TransientModel):
    _name = 'company.financial.summary'
    _description = 'Company Financial Summary'
    _transient = True


    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    actual_liquidity = fields.Monetary(string='Actual Liquidity', currency_field='company_currency', compute='_compute_financial_summary',)

    # Transaction Breakdown
    positive_transactions = fields.Monetary(string='Positive Transactions', currency_field='company_currency', compute='_compute_financial_summary',)
    negative_transactions = fields.Monetary(string='Negative Transactions', currency_field='company_currency', compute='_compute_financial_summary',)

    # investments Statistics
    investments_count = fields.Integer(string='investments Count', compute='_compute_financial_summary',)
    investments_open_count = fields.Integer(string='Open Investments Count', compute='_compute_financial_summary',)
    investments_closed_count = fields.Integer(string='Closed Investments Count', compute='_compute_financial_summary',)
    investments_total_amount = fields.Monetary(string='Total Investments Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    investments_open_amount = fields.Monetary(string='Open Investments Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    investments_closed_amount = fields.Monetary(string='Closed Investments Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    investments_maximum_amount = fields.Monetary(string='Maximum Investments Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    investments_minimum_amount = fields.Monetary(string='Minimum Investments Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    # Partnership Statistics
    Partnership_partners_count = fields.Integer(string='Partnership Partners Count', compute='_compute_financial_summary',)
    partnerships_debtor_amount = fields.Monetary(string='Total Debtor Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    
    # Partners Statistics
    partners_count = fields.Integer(string='Count Of All', compute='_compute_financial_summary')
    partners_active_count = fields.Integer(string='Count Of Active', compute='_compute_financial_summary',)
    partners_exited_count = fields.Integer(string='Count Of Exited', compute='_compute_financial_summary',)
    partners_debtor_count = fields.Integer(string='Count Of Debtors', compute='_compute_financial_summary',)
    partners_current_balance = fields.Monetary(string='Current Balance', currency_field='company_currency', compute='_compute_financial_summary',)
    partners_maximum_balance = fields.Monetary(string='Maximum Balance', currency_field='company_currency', compute='_compute_financial_summary',)
    partners_minimum_balance = fields.Monetary(string='Minimum Balance', currency_field='company_currency', compute='_compute_financial_summary',)
    partners_debtor_balance = fields.Monetary(string='Debtor Balance', currency_field='company_currency', compute='_compute_financial_summary',)

    # Purchases Statistics
    purchases_total_price = fields.Monetary(string='Purchases Total Price', currency_field='company_currency', compute='_compute_financial_summary',)
    purchases_paid_amount = fields.Monetary(string='Purchases Paid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    purchases_unpaid_amount = fields.Monetary(string='Purchases Unpaid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    purchases_paid_count = fields.Integer(string='Purchases Paid Count', compute='_compute_financial_summary',)
    purchases_unpaid_count = fields.Integer(string='Purchases Unpaid Count', compute='_compute_financial_summary',)
    purchases_count = fields.Integer(string='Purchase Count', compute='_compute_financial_summary',)
    
    # Sales Statistics
    sales_count = fields.Integer(string='Sales Count', compute='_compute_financial_summary',)
    sales_total_price = fields.Monetary(string='Sales Total Price', currency_field='company_currency', compute='_compute_financial_summary',)
    sales_total_profit = fields.Monetary(string='Sales Total Profit', currency_field='company_currency', compute='_compute_financial_summary',)
    sales_total_management_fees = fields.Monetary(string='Sales Total Management Fees', currency_field='company_currency', compute='_compute_financial_summary',)
    sales_paid_count = fields.Integer(string='Sales Paid Count', compute='_compute_financial_summary',)
    sales_unpaid_count = fields.Integer(string='Sales Unpaid Count', compute='_compute_financial_summary',)
    sales_paid_amount = fields.Monetary(string='Sales Paid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    sales_unpaid_amount = fields.Monetary(string='Sales Unpaid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    sales_total_net_profit = fields.Monetary(string='Sales Total Net Profit', currency_field='company_currency', compute='_compute_financial_summary',)
    
    # Expenses Statistics
    expenses_count = fields.Integer(string='Expenses Count', compute='_compute_financial_summary',)
    expenses_total_amount = fields.Monetary(string='Expenses Total Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    expenses_investment_count = fields.Integer(string='Investment Expenses Count', compute='_compute_financial_summary',)
    expenses_investment_amount = fields.Monetary(string='Investment Expenses Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    expenses_company_count = fields.Integer(string='Company Expenses Count', compute='_compute_financial_summary',)
    expenses_company_amount = fields.Monetary(string='Company Expenses Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    
    # Expenses Payment Status
    expenses_investment_paid_count = fields.Integer(string='Investment Expenses Paid Count', compute='_compute_financial_summary',)
    expenses_investment_paid_amount = fields.Monetary(string='Investment Expenses Paid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    expenses_investment_unpaid_count = fields.Integer(string='Investment Expenses Unpaid Count', compute='_compute_financial_summary',)
    expenses_investment_unpaid_amount = fields.Monetary(string='Investment Expenses Unpaid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    expenses_company_paid_count = fields.Integer(string='Company Expenses Paid Count', compute='_compute_financial_summary',)
    expenses_company_paid_amount = fields.Monetary(string='Company Expenses Paid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    expenses_company_unpaid_count = fields.Integer(string='Company Expenses Unpaid Count', compute='_compute_financial_summary',)
    expenses_company_unpaid_amount = fields.Monetary(string='Company Expenses Unpaid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    expenses_paid_count = fields.Integer(string='Expenses Paid Count', compute='_compute_financial_summary',)
    expenses_paid_amount = fields.Monetary(string='Expenses Paid Amount', currency_field='company_currency', compute='_compute_financial_summary',)
    expenses_unpaid_count = fields.Integer(string='Expenses Unpaid Count', compute='_compute_financial_summary',)
    expenses_unpaid_amount = fields.Monetary(string='Expenses Unpaid Amount', currency_field='company_currency', compute='_compute_financial_summary',)

    # Date Filter
    date_from = fields.Date(string='Date From', default=fields.Date.today)

    @api.depends('date_from')
    def _compute_financial_summary(self):
        """Compute all financial summary fields"""
        for record in self:
            # Get all relevant records
            partners = self.env['res.partner'].search([('is_partner', '=', True)])
            properties = self.env['real.estate.property'].search([])
            expenses = self.env['real.estate.expense'].search([])
            investments = self.env['real.estate.investment'].search([])
            partnerships = self.env['real.estate.partnership'].search([('status', '=', 'opening')])
            transactions = self.env['real.estate.transaction'].search([])            

            # investments Statistics ==========================================
            record.investments_count = len(investments)
            record.investments_open_count = len(investments.filtered(lambda d: d.status == 'opening'))
            record.investments_closed_count = len(investments.filtered(lambda d: d.status == 'closed'))

            record.investments_total_amount = sum(investment.total_investment_cost for investment in investments)
            record.investments_open_amount = sum(investment.total_investment_cost for investment in investments.filtered(lambda d: d.status == 'opening'))
            record.investments_closed_amount = sum(investment.total_investment_cost for investment in investments.filtered(lambda d: d.status == 'closed'))

            record.investments_maximum_amount = max(investment.total_investment_cost for investment in investments) if investments else 0
            record.investments_minimum_amount = min(investment.total_investment_cost for investment in investments) if investments else 0

            record.Partnership_partners_count = len(partnerships.mapped('partner_id'))
            record.partnerships_debtor_amount = sum(partnership.remaining_amount for partnership in partnerships if partnership.remaining_amount > 0)
            # Partners Statistics ========================================  
            record.partners_count = len(partners)
            record.partners_active_count = len(partners.filtered(lambda p: p.status == 'active'))
            record.partners_exited_count = len(partners.filtered(lambda p: p.status == 'exited'))
            record.partners_debtor_count = len(partners.filtered(lambda p: p.current_balance < 0))

            record.partners_current_balance = sum(partner.current_balance for partner in partners)
            record.partners_maximum_balance = max(partner.current_balance for partner in partners) if partners else 0
            record.partners_minimum_balance = min(partner.current_balance for partner in partners) if partners else 0
            record.partners_debtor_balance = abs(sum(partner.current_balance for partner in partners if partner.current_balance < 0))
            
            # Purchases Statistics =================================================
            purchaseProperties = properties.filtered(lambda p: p.is_purchased and p.status == 'confirmed')
            record.purchases_count = len(purchaseProperties)
            record.purchases_paid_count = len(purchaseProperties.filtered(lambda p: p.remaining_amount <= 0))
            record.purchases_unpaid_count = len(purchaseProperties.filtered(lambda p: p.remaining_amount > 0))

            record.purchases_total_price = sum(p.property_price for p in purchaseProperties)
            record.purchases_paid_amount = sum(p.property_price - p.remaining_amount for p in purchaseProperties)
            record.purchases_unpaid_amount = sum(p.remaining_amount for p in purchaseProperties)

            # Sales Statistics ==================================================
            salesProperties = properties.filtered(lambda p: not p.is_purchased and p.status == 'confirmed')

            record.sales_count = len(salesProperties)
            record.sales_total_price = sum(sale.property_price for sale in salesProperties)

            record.sales_paid_count = len(salesProperties.filtered(lambda s: s.remaining_amount <= 0))
            record.sales_unpaid_count = len(salesProperties.filtered(lambda s: s.remaining_amount > 0))

            record.sales_paid_amount = sum(sale.property_price - sale.remaining_amount for sale in salesProperties)
            record.sales_unpaid_amount = sum(sale.remaining_amount for sale in salesProperties)

            record.sales_total_profit = sum(sale.total_profit for sale in salesProperties)
            record.sales_total_management_fees = sum(sale.management_fee_amount for sale in salesProperties)
            record.sales_total_net_profit = sum(sale.net_profit for sale in salesProperties)

            # Expenses Statistics ===========================================================
            investment_expenses = expenses.filtered(lambda e: e.expense_type == 'investment')
            company_expenses = expenses.filtered(lambda e: e.expense_type == 'company')

            record.expenses_count = len(expenses)
            record.expenses_total_amount = sum(expense.amount for expense in expenses)

            record.expenses_investment_count = len(investment_expenses)
            record.expenses_investment_amount = sum(expense.amount for expense in investment_expenses)

            record.expenses_company_count = len(company_expenses)
            record.expenses_company_amount = sum(expense.amount for expense in company_expenses)

            record.expenses_paid_count = len(expenses.filtered(lambda e: e.status == 'paid'))
            record.expenses_paid_amount = sum(expense.amount for expense in expenses if expense.status == 'paid')

            record.expenses_unpaid_count = len(expenses.filtered(lambda e: e.status != 'paid'))
            record.expenses_unpaid_amount = sum(e.amount for e in expenses if e.status != 'paid')
            #-------------------------------
            record.expenses_investment_paid_count = len(investment_expenses.filtered(lambda e: e.status == 'paid'))
            record.expenses_investment_paid_amount = sum(e.amount for e in investment_expenses if e.status == 'paid')

            record.expenses_investment_unpaid_count = len(investment_expenses.filtered(lambda e: e.status != 'paid'))
            record.expenses_investment_unpaid_amount = sum(e.amount for e in investment_expenses if e.status != 'paid')
            #-------------------------------
            record.expenses_company_paid_count = len(company_expenses.filtered(lambda e: e.status == 'paid'))
            record.expenses_company_paid_amount = sum(e.amount for e in company_expenses if e.status == 'paid')

            record.expenses_company_unpaid_count = len(company_expenses.filtered(lambda e: e.status != 'paid'))
            record.expenses_company_unpaid_amount = sum(e.amount for e in company_expenses if e.status != 'paid')

            # Actual Liquidity ===================================================
            record.positive_transactions = sum(t.amount for t in transactions if t.transaction_type != 'withdrawal')
            record.negative_transactions = sum(t.amount for t in transactions if t.transaction_type == 'withdrawal')
            record.actual_liquidity = (
                record.positive_transactions 
                - record.negative_transactions 
                - record.expenses_paid_amount
                - record.purchases_paid_amount
                + record.sales_paid_amount
            )
            

    def action_print_report(self):
        """Print the financial summary report"""
        return self.env.ref('real_estate_partnership_management_pro.action_report_company_financial_summary').report_action(self)
