# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import _


class PartnerUnifiedLedger(models.TransientModel):
    _name = 'partner.unified.ledger'
    _description = 'Partner Unified Ledger with All Transactions'

    partner_id = fields.Many2one('real.estate.partner', string='Partner', required=True, readonly=True)
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    line_ids = fields.One2many('partner.unified.ledger.line', 'ledger_id', string='Unified Ledger Lines')

    @api.model
    def default_get(self, fields_list):
        res = super(PartnerUnifiedLedger, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            partner = self.env['real.estate.partner'].browse(active_id)
            res['partner_id'] = partner.id
            # default date range: from join_date to today
            res['date_from'] = partner.join_date or False
            res['date_to'] = fields.Date.today()
        return res

    def _build_unified_ledger(self):
        """
        Build unified ledger lines combining:
        - real.estate.transaction (deposits, withdrawals, profits, expenses, investment returns)
        - real.estate.expense.distribution (company expense allocations)
        - real.estate.partner.exit.lines (exit profits)
        - real.estate.property.sale.line (sale profits)

        All lines are sorted by date and a running balance is calculated.
        """
        self.ensure_one()
        partner = self.partner_id
        date_from = self.date_from
        date_to = self.date_to

        # Collect all transactions from different models
        all_items = []

        # ============ 1. Transactions (real.estate.transaction) ============
        tx_domain = [('partner_id', '=', partner.id)]
        if date_from:
            tx_domain.append(('transaction_date', '>=', date_from))
        if date_to:
            tx_domain.append(('transaction_date', '<=', date_to))

        transactions = self.env['real.estate.transaction'].search(tx_domain)
        for tx in transactions:
            # Calculate signed amount
            if tx.transaction_type in ['deposit', 'profit_distribution', 'investment_return']:
                amount = float(tx.amount)
            else:  # withdrawal, expense
                amount = -float(tx.amount)

            all_items.append({
                'date': tx.transaction_date,
                'source': 'transaction',
                'source_id': tx.id,
                'name': tx.name,
                'transaction_type': tx.transaction_type,
                'description': tx.description or '',
                'amount': amount,
            })

        # ============ 2. Expense Distributions (real.estate.expense.distribution) ============
        exp_domain = [('partner_id', '=', partner.id)]
        if date_from:
            exp_domain.append(('distribution_date', '>=', date_from))
        if date_to:
            exp_domain.append(('distribution_date', '<=', date_to))

        try:
            expense_distrs = self.env['real.estate.expense.distribution'].search(exp_domain)
            for exp_dist in expense_distrs:
                all_items.append({
                    'date': exp_dist.distribution_date,
                    'source': 'expense_distribution',
                    'source_id': exp_dist.id,
                    'name': exp_dist.expense_id.name,
                    'transaction_type': exp_dist.expense_id.category_id.name,
                    'description': _('Expense Distribution'),
                    'amount': -float(exp_dist.partner_share),  # Negative because it reduces balance
                })
        except Exception:
            pass  # Model may not have distribution_date field

        # ============ 3. Exit Lines (real.estate.partner.exit.lines) ============
        exit_domain = [('partner_id', '=', partner.id)]
        if date_from:
            exit_domain.append(('exit_date', '>=', date_from))
        if date_to:
            exit_domain.append(('exit_date', '<=', date_to))

        try:
            exit_lines = self.env['real.estate.partner.exit.lines'].search(exit_domain)
            for exit_line in exit_lines:
                all_items.append({
                    'date': exit_line.exit_date,
                    'source': 'exit_line',
                    'source_id': exit_line.id,
                    'name': exit_line.name,
                    'transaction_type': 'exit_profit',
                    'description': _('Exit Profit'),
                    'amount': float(exit_line.profit_amount),  # Positive
                })
        except Exception:
            pass

        # ============ 4. Property Sale Lines (real.estate.property.sale.line) ============
        sale_domain = [('partner_id', '=', partner.id)]
        if date_from:
            sale_domain.append(('sale_date', '>=', date_from))
        if date_to:
            sale_domain.append(('sale_date', '<=', date_to))
        try:
            sale_lines = self.env['real.estate.property.sale.line'].search(sale_domain)
            for sale_line in sale_lines:
                all_items.append({
                    'date': sale_line.sale_date,
                    'source': 'sale_line',
                    'source_id': sale_line.id,
                    'name': sale_line.sale_id.name,
                    'transaction_type': 'sale_profit',
                    'description': _('Sale Profit'),
                    'amount': float(sale_line.profit_amount),  # Positive
                })
        except Exception:
            pass

        # ============ Sort by date and calculate opening balance ============
        all_items.sort(key=lambda x: (x['date'], x['source_id']))

        # Calculate opening balance (sum of all items before date_from)
        opening_balance = 0.0
        if date_from:
            opening_domain = [('partner_id', '=', partner.id)]
            opening_domain.append(('transaction_date', '<', date_from))
            opening_txs = self.env['real.estate.transaction'].search(opening_domain)
            for tx in opening_txs:
                if tx.transaction_type in ['deposit', 'profit_distribution', 'investment_return']:
                    opening_balance += float(tx.amount)
                else:
                    opening_balance -= float(tx.amount)

            # Also add opening balances from other sources before date_from
            try:
                opening_exps = self.env['real.estate.expense.distribution'].search(
                    [('partner_id', '=', partner.id), ('distribution_date', '<', date_from)]
                )
                for exp_dist in opening_exps:
                    opening_balance -= float(exp_dist.partner_share)
            except Exception:
                pass

            try:
                opening_exits = self.env['real.estate.partner.exit.lines'].search(
                    [('partner_id', '=', partner.id), ('exit_date', '<', date_from)]
                )
                for exit_line in opening_exits:
                    opening_balance += float(exit_line.profit_amount)
            except Exception:
                pass

            try:
                opening_sales = self.env['real.estate.property.sale.line'].search(
                    [('partner_id', '=', partner.id), ('sale_date', '<', date_from)]
                )
                for sale_line in opening_sales:
                    opening_balance += float(sale_line.profit_amount)
            except Exception:
                pass

        # ============ Create ledger lines ============
        lines = []
        running_balance = opening_balance

        # Add opening balance line if there's a range
        if date_from and opening_balance != 0.0:
            lines.append((0, 0, {
                'date': date_from,
                'name': _('Opening Balance'),
                'transaction_type': 'opening_balance',
                'description': _('Balance brought forward'),
                'amount': opening_balance,
                'balance': running_balance,
                'ledger_id': self.id,
            }))

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
                'ledger_id': self.id,
            }))

        # Create lines if any
        self.line_ids.unlink()
        self.line_ids = lines

    def action_view_tree_ledger(self):
        """Button action to (re)compute unified ledger lines"""
        self._build_unified_ledger()
        return {
            'name': _('Unified Ledger'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.unified.ledger.line',
            'domain': [('ledger_id', '=', self.id)],
            'view_mode': 'tree',
        }

    def action_print_report(self):
        """Build ledger (if needed) and return the PDF report action for this wizard."""
        self.ensure_one()
        # make sure lines are up-to-date
        self._build_unified_ledger()
        # Use the report defined in XML to generate the PDF
        return self.env.ref('real_estate_partnership_management.report_partner_unified_ledger_action').report_action(self)


class PartnerUnifiedLedgerLine(models.TransientModel):
    _name = 'partner.unified.ledger.line'
    _description = 'Partner Unified Ledger Line'

    ledger_id = fields.Many2one('partner.unified.ledger', string='Ledger', ondelete='cascade')
    date = fields.Date(string='Date')
    source = fields.Char(string='Source Type')  # transaction, expense_distribution, exit_line, sale_line
    source_id = fields.Integer(string='Source ID')
    name = fields.Char(string='Reference/Description')
    transaction_type = fields.Char(string='Type')
    description = fields.Text(string='Details')
    amount = fields.Float(string='Amount', digits=(12, 2))
    balance = fields.Float(string='Balance', digits=(12, 2))

