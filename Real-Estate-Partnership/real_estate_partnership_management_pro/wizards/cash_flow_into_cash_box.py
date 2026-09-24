# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import _


class CashFlowIntoCashBox(models.TransientModel):
    _name = 'cash.flow.into.cash.box'
    _description = 'Cash Flow Into Cash Box'

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    line_ids = fields.One2many('cash.flow.into.cash.box.line', 'cash_box_id', string='Cash Flow Lines')


    def _build_cash_flow_into_cash_box(self):
        self.ensure_one()
        date_from = self.date_from
        date_to = self.date_to

        # Collect all transactions from different models
        all_items = []

        # 1. All Transactions (real.estate.transaction)
        transactions = self.env['real.estate.transaction'].search([])
        match_transactions = transactions.filtered(lambda x: (not date_from or x.transaction_date >= date_from) and (not date_to or x.transaction_date <= date_to))
        for tx in match_transactions:
            all_items.append({
                'date': tx.transaction_date,
                'source': 'transaction',
                'source_id': tx.id,
                'name': tx.name,
                'transaction_type': tx.transaction_type,
                'description': tx.description or '',
                'amount': -tx.amount if tx.transaction_type == 'withdrawal' else tx.amount,
            })

        # 2. Paid Expenses (real.estate.expense)
        paid_expenses = self.env['real.estate.expense'].search([('status', '=', 'paid'),('paid_date', '!=', False)])
        match_paid_expenses = paid_expenses.filtered(lambda x: (not date_from or x.paid_date >= date_from) and (not date_to or x.paid_date <= date_to))
        for expense in match_paid_expenses:
            all_items.append({
                'date': expense.paid_date,
                'source': 'expense',
                'source_id': expense.id,
                'name': expense.code,
                'transaction_type': expense.expense_type,
                'description': expense.name or '',
                'amount': -expense.amount,  # Negative for expenses
            })

        # 3. Confirmed Properties (real.estate.property)
        conformed_properties = self.env['real.estate.property'].search([('status', '=', 'confirmed')])
        match_properties = conformed_properties.filtered(lambda x: (not date_from or x.property_date >= date_from) and (not date_to or x.property_date <= date_to))
        for prop in match_properties:
            type_prop = _('Purchased') if prop.is_purchased else _('Sold')
            all_items.append({
                'date': prop.property_date,
                'source': 'Down Payment Property',
                'source_id': prop.id,
                'name': prop.name,
                'transaction_type': 'Down Payment',
                'description': _('Property %s: %s') % (type_prop,prop.name),
                'amount': prop.down_payment if not prop.is_purchased else -prop.down_payment,
            })

        # 4. Paid payment installments of properties (real.estate.payment.installment)
        paid_installments = match_properties.mapped('payment_ids').filtered(lambda x: x.status == 'paid' and x.paid_date)
        match_paid_installments = paid_installments.filtered(lambda x: (not date_from or x.paid_date >= date_from) and (not date_to or x.paid_date <= date_to))
        for installment in match_paid_installments:
            type_installment = _('Purchase') if installment.is_purchased else _('Sale')
            all_items.append({
                'date': installment.paid_date,
                'source': 'Sale Installment',
                'source_id': installment.id,
                'name': installment.name,
                'transaction_type': 'Paid Installment',
                'description': _('Paid %s Installment: %s') % (type_installment,installment.name),
                'amount': installment.amount if not installment.is_purchased else -installment.amount,
            })

        # Calculate opening balance (sum of all items before date_from)
        opening_balance = 0.0
        running_balance = 0.0
        lines = []
        if date_from:
            opening_transactions_postv = transactions.filtered(lambda x: x.transaction_date < date_from and x.transaction_type != 'withdrawal')
            opening_balance += sum(transaction.amount for transaction in opening_transactions_postv)

            opening_transactions_ngtv = transactions.filtered(lambda x: x.transaction_date < date_from and x.transaction_type == 'withdrawal')
            opening_balance -= sum(transaction.amount for transaction in opening_transactions_ngtv)

            opening_expenses = paid_expenses.filtered(lambda x: x.paid_date < date_from)
            opening_balance -= sum(expense.amount for expense in opening_expenses)

            opening_conformed_properties_sale = conformed_properties.filtered(lambda x: x.property_date < date_from and x.is_purchased == False)
            opening_balance += sum(property.down_payment for property in opening_conformed_properties_sale)

            opening_conformed_properties_purchase = conformed_properties.filtered(lambda x: x.property_date < date_from and x.is_purchased)
            opening_balance -= sum(property.down_payment for property in opening_conformed_properties_purchase)

            opening_paid_installments_sale = paid_installments.filtered(lambda x: x.paid_date < date_from and not x.is_purchased)
            opening_balance += sum(installment.amount for installment in opening_paid_installments_sale)

            opening_paid_installments_purchase = paid_installments.filtered(lambda x: x.paid_date < date_from and x.is_purchased == True)
            opening_balance -= sum(installment.amount for installment in opening_paid_installments_purchase)

            # Add opening balance line if there's a range
            if opening_balance != 0.0:
                running_balance = opening_balance
                lines.append((0, 0, {
                    'date': date_from,
                    'name': _('Opening Balance'),
                    'transaction_type': 'opening_balance',
                    'description': _('Balance brought forward'),
                    'amount': opening_balance,
                    'balance': running_balance,
                    'cash_box_id': self.id,
                }))

        # Sort by date and source
        all_items.sort(key=lambda x: (x['date'], x['source_id']))
        # Add transaction lines
        for item in all_items:
            amt = item['amount']
            running_balance += amt
            lines.append((0, 0, {
                'date': item['date'],
                'source': item['source'],
                'source_id': item['source_id'],
                'name': item['name'],
                'transaction_type': item['transaction_type'],
                'description': item['description'],
                'amount': amt,
                'balance': running_balance,
                'cash_box_id': self.id,
            }))

        # Create lines if any
        self.line_ids.unlink()
        self.line_ids = lines

    def action_view_tree_ledger(self):
        """Button action to (re)compute unified ledger lines"""
        self._build_cash_flow_into_cash_box()
        return {
            'name': _('Daily Cashbox'),
            'type': 'ir.actions.act_window',
            'res_model': 'cash.flow.into.cash.box.line',
            'domain': [('cash_box_id', '=', self.id)],
            'view_mode': 'tree',
        }

    def action_print_report(self):
        """Build ledger (if needed) and return the PDF report action for this wizard."""
        self.ensure_one()
        self._build_cash_flow_into_cash_box()
        return self.env.ref('real_estate_partnership_management_pro.action_report_cash_flow_into_cash_box').report_action(self)


class CashFlowIntoCashBoxLine(models.TransientModel):
    _name = 'cash.flow.into.cash.box.line'
    _description = 'Cash Flow Into Cash Box Line'

    cash_box_id = fields.Many2one('cash.flow.into.cash.box', string='Cash Box', ondelete='cascade')
    company_currency = fields.Many2one("res.currency", string='Currency', default=lambda self: self.env.company.currency_id,)
    date = fields.Date(string='Date')
    source = fields.Char(string='Source Type')  # transaction, expenses, properties, installments
    source_id = fields.Integer(string='Source ID')
    name = fields.Char(string='Reference/Description')
    transaction_type = fields.Char(string='Type')
    description = fields.Text(string='Details')
    amount = fields.Monetary(string='Amount', currency_field='company_currency')
    balance = fields.Monetary(string='Balance', currency_field='company_currency')

