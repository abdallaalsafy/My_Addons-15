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

    # Deals Statistics
    deals_count = fields.Integer(string='Deals Count', compute='_compute_financial_summary', store=True)
    deals_open_count = fields.Integer(string='Deals Open Count', compute='_compute_financial_summary', store=True)
    deals_closed_count = fields.Integer(string='Deals Closed Count', compute='_compute_financial_summary', store=True)
    deals_total_amount = fields.Float(string='Deals Total Amount', compute='_compute_financial_summary', store=True)
    deals_open_amount = fields.Float(string='Deals Open Amount', compute='_compute_financial_summary', store=True)
    deals_closed_amount = fields.Float(string='Deals Closed Amount', compute='_compute_financial_summary
    deals_maximum_amount = fields.Float(string='Deals Maximum Amount', compute='_compute_financial_summary', store=True)
    deals_minimum_amount = fields.Float(string='Deals Minimum Amount', compute='_compute_financial_summary', store=True)
    # Partnership Statistics
    Partnership_partners_count = fields.Integer(string='Partnership Partners Count', compute='_compute_financial_summary', store=True)
    partnerships_debtor_amount = fields.Float(string='Total Debtor Amount', compute='_compute_financial_summary', store=True)
    
    # Partners Statistics
    partners_count = fields.Integer(string='Partners Count', compute='_compute_financial_summary', store=True)
    partners_active_count = fields.Integer(string='Partners Active Count', compute='_compute_financial_summary', store=True)
    partners_exited_count = fields.Integer(string='Partners Exited Count', compute='_compute_financial_summary', store=True)
    partners_debtor_count = fields.Integer(string='Partners Debtor Count', compute='_compute_financial_summary', store=True)
    partners_current_balance = fields.Float(string='Partners Current Balance', compute='_compute_financial_summary',
                                               store=True)
    partners_maximum_balance = fields.Float(string='Partners Maximum Balance', compute='_compute_financial_summary', store=True)
    partners_minimum_balance = fields.Integer(string='Partners Minimum Balance', compute='_compute_financial_summary', store=True)
    partners_debtor_balance = fields.Float(string='Partners Debtor Balance', compute='_compute_financial_summary', store=True)

    # contracts Statistics
    purchases_total_price = fields.Float(string='Purchases Total Price', compute='_compute_financial_summary', store=True)
    purchases_paid_amount = fields.Integer(string='Purchases Paid Amount', compute='_compute_financial_summary', store=True)
    purchases_unpaid_amount = fields.Integer(string='Purchases Unpaid Amount', compute='_compute_financial_summary', store=True)
    purchases_paid_count = fields.Integer(string='Purchases Paid Count', compute='_compute_financial_summary', store=True)
    purchases_unpaid_count = fields.Integer(string='Purchases Unpaid Count', compute='_compute_financial_summary', store=True)
    purchases_count = fields.Integer(string='Purchase Count', compute='_compute_financial_summary', store=True)
    
    # Sales Statistics
    sales_count = fields.Integer(string='Sales Count', compute='_compute_financial_summary', store=True)
    sales_total_price = fields.Float(string='Sales Total Price', compute='_compute_financial_summary', store=True)
    sales_total_profit = fields.Float(string='Sales Total Profit', compute='_compute_financial_summary', store=True)
    sales_total_management_fees = fields.Float(string='Sales Total Management Fees', compute='_compute_financial_summary', store=True)
    sales_paid_count = fields.Integer(string='Sales Paid Count', compute='_compute_financial_summary', store=True)
    sales_unpaid_count = fields.Integer(string='Sales Unpaid Count', compute='_compute_financial_summary', store=True)
    sales_paid_amount = fields.Integer(string='Sales Paid Amount', compute='_compute_financial_summary', store=True)
    sales_unpaid_amount = fields.Integer(string='Sales Unpaid Amount', compute='_compute_financial_summary', store=True)
    sales_total_net_profit = fields.Float(string='Sales Total Net Profit', compute='_compute_financial_summary', store=True)
    
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

    # Date Filter
    date_from = fields.Date(string='Date From', default=fields.Date.today)

    @api.depends('date_from')
    def _compute_financial_summary(self):
        """Compute all financial summary fields"""
        for record in self:
            # Get all relevant records
            partners = self.env['res.partner'].search([('is_partner', '=', True)])
            contracts = self.env['real.estate.property'].search([])
            expenses = self.env['real.estate.expense'].search([])
            deals = self.env['real.estate.property.deal'].search([])
            partnerships = self.env['real.estate.partnership'].search([('status', '=', 'opening')])
            transactions = self.env['res.partner.transaction'].search([])
            payments_installments = self.env['real.estate.payment.installment'].search([])
            
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
                for property in contracts
                if property.status == 'sold' and property.is_child and property.parent_id.status != 'sold'
            )
            # 3. Property Assets (total_cost)
            record.property_assets = sum(
                property.total_cost 
                for property in contracts 
                if property.status != 'sold' and property.is_child == False
            )
            
            # 4. Positive Transactions
            record.positive_transactions = sum(t.amount for t in transactions if t.transaction_type != 'withdrawal')
            # 5. Negative Transactions
            record.negative_transactions = sum(t.amount for t in transactions if t.transaction_type == 'withdrawal')
            # 6.0 Paid Expense
            record.expense_paid = sum(expense.amount for expense in expenses if expense.status == 'paid')
            
            # 7. Undistributed Company Expenses
            record.undistributed_company_expenses = sum(
                expense.amount 
                for expense in expenses 
                if expense.expense_type == 'company' and not expense.distribution_ids
            )
            
            # 8. Purchase Paid
            record.purchase_paid = sum(p.amount for p in payments_installments if p.status == 'paid' and p.is_purchase)
            # 9. Sale Paid
            record.sale_paid = sum(p.amount for p in payments_installments if p.status == 'paid' and not p.is_purchase)
            
            # 10. Property Expenses Paid
            record.property_expenses_paid = sum(
                exp.amount 
                for exp in expenses 
                if exp.expense_type == 'investment' and exp.status == 'paid'
            )
            
            # 11. Total Company Balance
            record.total_company_balance = record.partners_actual_balance + record.management_fees + record.property_assets - record.sold_child_property_assets - record.undistributed_company_expenses
            
            

            # Deals Statistics ==========================================
            record.deals_count = len(deals)
            record.deals_open_count = len(deals.filtered(lambda d: d.status == 'opening'))
            record.deals_closed_count = len(deals.filtered(lambda d: d.status == 'closed'))

            record.deals_total_amount = sum(deal.total_deal_cost for deal in deals)
            record.deals_open_amount = sum(deal.total_deal_cost for deal in deals.filtered(lambda d: d.status == 'opening'))
            record.deals_closed_amount = sum(deal.total_deal_cost for deal in deals.filtered(lambda d: d.status == 'closed'))

            record.deals_maximum_amount = max(deal.total_deal_cost for deal in deals) if deals else 0
            record.deals_minimum_amount = min(deal.total_deal_cost for deal in deals) if deals else 0

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


            record.partners_total_investments = sum(
                partner.confirmed_investments_total 
                for partner in partners
            )
            
            record.partners_negative_actual_balance_total = abs(sum(
                partner.actual_balance
                for partner in partners 
                if partner.actual_balance < 0
            ))
            record.partners_negative_actual_balance_count = len(
                [partner for partner in partners if partner.actual_balance < 0]
            )
            
            
            # Purchases Statistics =================================================
            purchaseContracts = contracts.filtered(lambda p: p.is_purchased and p.status == 'confirmed')
            record.purchases_count = len(purchaseContracts)
            record.purchases_paid_count = len(purchaseContracts.filtered(lambda p: p.remaining_amount <= 0))
            record.purchases_unpaid_count = len(purchaseContracts.filtered(lambda p: p.remaining_amount > 0))

            record.purchases_total_price = sum(p.contract_price for p in purchaseContracts)
            record.sales_paid_amount = sum(p.contract_price - p.remaining_amount for p in purchaseContracts)
            record.sales_unpaid_amount = sum(p.remaining_amount for p in purchaseContracts)

            # Sales Statistics ==================================================
            salesContracts = contracts.filtered(lambda p: not p.is_purchased and p.status == 'confirmed')

            record.sales_count = len(salesContracts)
            record.sales_total_price = sum(sale.contract_price for sale in salesContracts)

            record.sales_paid_count = len(salesContracts.filtered(lambda s: s.remaining_amount <= 0))
            record.sales_unpaid_count = len(salesContracts.filtered(lambda s: s.remaining_amount > 0))

            record.sales_paid_amount = sum(sale.contract_price - sale.remaining_amount for sale in salesContracts)
            record.sales_unpaid_amount = sum(sale.remaining_amount for sale in salesContracts)

            record.sales_total_profit = sum(sale.total_profit for sale in salesContracts)
            record.sales_total_management_fees = sum(sale.management_fee_amount for sale in salesContracts)
            record.sales_total_net_profit = sum(sale.net_profit for sale in salesContracts)
            
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
            record.expense_paid = sum(expense.amount for expense in expenses if expense.status == 'paid')

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
            record.actual_liquidity = (
                record.partners_current_balance
                - record.expense_paid
                - record.purchase_paid
                + record.sale_paid
            )
            

    def action_print_report(self):
        """Print the financial summary report"""
        return self.env.ref('real_estate_partnership_management_pro.action_report_company_financial_summary').report_action(self)
