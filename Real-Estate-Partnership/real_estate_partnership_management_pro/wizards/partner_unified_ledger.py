# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import _


class PartnerUnifiedLedger(models.TransientModel):
    _name = 'partner.unified.ledger'
    _description = 'Partner Unified Ledger with All Transactions'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, readonly=True)
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    line_ids = fields.One2many('partner.unified.ledger.line', 'ledger_id', string='Unified Ledger Lines')

    @api.model
    def default_get(self, fields_list):
        res = super(PartnerUnifiedLedger, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            partner = self.env['res.partner'].browse(active_id)
            res['partner_id'] = active_id
            # default date range: from join_date to today
            res['date_from'] = partner.join_date or False
            res['date_to'] = fields.Date.today()
        return res

    def _build_unified_ledger(self):
        self.ensure_one()
        partner = self.partner_id
        date_from = self.date_from
        date_to = self.date_to

        # Collect all transactions from different models
        all_items = []

        # 1. Transactions (real.estate.transaction)
        transactions = partner.transaction_ids.filtered(lambda x: x.transaction_date <= date_to and x.transaction_date >= date_from)
        for tx in transactions:
            if tx.transaction_type == 'withdrawal':
                amount = -tx.amount
            else:
                amount = tx.amount
            all_items.append({
                'date': tx.transaction_date,
                'source': 'transaction',
                'source_id': tx.id,
                'name': tx.name,
                'transaction_type': tx.transaction_type,
                'description': tx.description or '',
                'amount': amount,
            })

        # 2. Property Sale Lines (real.estate.property.sale.line)
        try:
            sale_lines = partner.sale_line_ids.filtered(lambda x: x.sale_date <= date_to and x.sale_date >= date_from)
            for sale_line in sale_lines:
                all_items.append({
                    'date': sale_line.contract_date,
                    'source': 'sale_line',
                    'source_id': sale_line.contract_id.id,
                    'name': sale_line.contract_id.name,
                    'transaction_type': 'sale_profit',
                    'description': _('Sale Profit'),
                    'amount': sale_line.profit_amount,  # Positive
                })
        except Exception:
            pass

        # Calculate opening balance (sum of all items before date_from)
        opening_balance = 0.0
        running_balance = 0.0
        lines = []
        if date_from:
            opening_txs = transactions = partner.transaction_ids.filtered(lambda x: x.transaction_date < date_from)
            for tx in opening_txs:
                if tx.transaction_type == 'withdrawal':
                    opening_balance -= tx.amount
                else:
                    opening_balance += tx.amount

            opening_sales = partner.sale_line_ids.filtered(lambda x: x.sale_date < date_from)
            opening_balance += sum(sale_line.profit_amount for sale_line in opening_sales)

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
                    'ledger_id': self.id,
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
        return self.env.ref('real_estate_partnership_management_pro.report_partner_unified_ledger_action').report_action(self)


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

