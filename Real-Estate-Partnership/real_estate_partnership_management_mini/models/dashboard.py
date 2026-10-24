# -*- coding: utf-8 -*-
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


# Fields of the "Company Financial Summary" wizard that the dashboard re-uses,
# so the dashboard numbers always match the printed report.
SUMMARY_FIELDS = [
    'actual_liquidity', 'positive_transactions', 'negative_transactions',
    'expenses_paid_amount', 'purchases_paid_amount', 'sales_paid_amount',
    'investments_count', 'investments_open_count', 'investments_closed_count',
    'investments_total_amount', 'investments_open_amount', 'investments_closed_amount',
    'partnerships_debtor_amount',
    'partners_count', 'partners_active_count', 'partners_exited_count',
    'partners_debtor_count', 'partners_current_balance', 'partners_debtor_balance',
    'purchases_count', 'purchases_total_price', 'purchases_unpaid_amount',
    'sales_count', 'sales_total_price', 'sales_total_profit',
    'sales_total_management_fees', 'sales_total_net_profit', 'sales_unpaid_amount',
    'expenses_count', 'expenses_total_amount',
    'expenses_unpaid_amount', 'expenses_investment_amount', 'expenses_company_amount',
]


class RealEstateDashboard(models.AbstractModel):
    _name = 'real.estate.dashboard'
    _description = 'Real Estate Dashboard Data'

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @api.model
    def _selection_labels(self, model, field_name):
        field = self.env[model]._fields[field_name]
        return dict(field._description_selection(self.env))

    @api.model
    def _month_keys(self, today, count=12):
        first = today.replace(day=1)
        months = [first - relativedelta(months=i) for i in range(count - 1, -1, -1)]
        return months, [m.strftime('%Y-%m') for m in months]

    @api.model
    def _sum_by_month(self, records, date_field, value_field, keys):
        totals = dict.fromkeys(keys, 0.0)
        for rec in records:
            day = rec.get(date_field)
            if not day:
                continue
            key = day.strftime('%Y-%m')
            if key in totals:
                totals[key] += rec.get(value_field) or 0.0
        return [round(totals[k], 2) for k in keys]

    @api.model
    def _summary_kpis(self):
        wizard = self.env['company.financial.summary'].create({})
        values = {}
        for name in SUMMARY_FIELDS:
            if name in wizard._fields:
                values[name] = wizard[name] or 0
        return values

    # ------------------------------------------------------------------
    # main entry point called by the OWL client action
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)
        currency = self.env.company.currency_id
        months, month_keys = self._month_keys(today)
        start = months[0]

        Investment = self.env['real.estate.investment']
        Property = self.env['real.estate.property']
        Expense = self.env['real.estate.expense']
        Installment = self.env['real.estate.payment.installment']
        Transaction = self.env['real.estate.transaction']

        # ---------------- investments ----------------
        inv_fields = [
            'name', 'code', 'status', 'investment_type', 'total_investment_cost',
            'total_area', 'sold_area', 'remaining_area', 'total_partnerships_percentage',
            'draft_sold_properties_count', 'purchased_properties_count',
        ]
        investments = Investment.search_read([], inv_fields)
        status_labels = self._selection_labels('real.estate.investment', 'status')
        type_labels = self._selection_labels('real.estate.investment', 'investment_type')

        by_status = defaultdict(int)
        by_type = defaultdict(float)
        for inv in investments:
            by_status[inv['status']] += 1
            by_type[inv['investment_type']] += inv['total_investment_cost'] or 0.0
        status_chart = {
            'labels': [status_labels.get(k, k) for k in by_status],
            'values': list(by_status.values()),
        }
        type_chart = {
            'labels': [type_labels.get(k, k) for k in by_type],
            'values': [round(v, 2) for v in by_type.values()],
        }

        open_invs = [i for i in investments if i['status'] == 'opening']
        area_rows = sorted(open_invs, key=lambda i: i['total_area'] or 0.0, reverse=True)[:8]
        area_chart = {
            'labels': [i['name'] or i['code'] for i in area_rows],
            'sold': [round(i['sold_area'] or 0.0, 2) for i in area_rows],
            'remaining': [round(i['remaining_area'] or 0.0, 2) for i in area_rows],
        }

        # ---------------- alerts (things that need an action) ----------------
        ready_to_close = [
            i['id'] for i in open_invs
            if (i['total_area'] or 0) > 0 and (i['remaining_area'] or 0) <= 0
            and not i['draft_sold_properties_count']
        ]
        restructure_ready = [
            i['id'] for i in open_invs
            if (i['total_area'] or 0) > 0 and (i['remaining_area'] or 0) <= 0
            and i['draft_sold_properties_count']
            and (i['total_partnerships_percentage'] or 0) >= 100
        ]
        incomplete_partnerships = [
            i['id'] for i in open_invs
            if i['purchased_properties_count'] and (i['total_partnerships_percentage'] or 0) < 100
        ]

        # ---------------- monthly series (last 12 months) ----------------
        purchases = Property.search_read(
            [('is_purchased', '=', True), ('property_date', '>=', start)],
            ['property_date', 'property_price'])
        sales = Property.search_read(
            [('is_purchased', '=', False), ('status', '=', 'confirmed'), ('property_date', '>=', start)],
            ['property_date', 'property_price'])
        sale_lines = self.env['real.estate.sale.line'].search_read(
            [('property_date', '>=', start)], ['property_date', 'profit_amount'])
        expenses = Expense.search_read([('expense_date', '>=', start)], ['expense_date', 'amount'])
        transactions = Transaction.search_read(
            [('transaction_date', '>=', start)], ['transaction_date', 'amount', 'transaction_type'])
        deposits = [t for t in transactions if t['transaction_type'] != 'withdrawal']
        withdrawals = [t for t in transactions if t['transaction_type'] == 'withdrawal']

        monthly = {
            'months': month_keys,
            'purchases': self._sum_by_month(purchases, 'property_date', 'property_price', month_keys),
            'sales': self._sum_by_month(sales, 'property_date', 'property_price', month_keys),
            'profits': self._sum_by_month(sale_lines, 'property_date', 'profit_amount', month_keys),
            'expenses': self._sum_by_month(expenses, 'expense_date', 'amount', month_keys),
            'deposits': self._sum_by_month(deposits, 'transaction_date', 'amount', month_keys),
            'withdrawals': self._sum_by_month(withdrawals, 'transaction_date', 'amount', month_keys),
        }

        # ---------------- expenses by category ----------------
        by_category = defaultdict(float)
        for exp in Expense.search_read([], ['category_id', 'amount']):
            name = exp['category_id'][1] if exp['category_id'] else _('Uncategorized')
            by_category[name] += exp['amount'] or 0.0
        ranked = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)
        rest = sum(value for _name, value in ranked[7:])
        categories = ranked[:7] + ([(_('Other'), rest)] if rest else [])
        category_chart = {
            'labels': [name for name, _value in categories],
            'values': [round(value, 2) for _name, value in categories],
        }

        # ---------------- partners ----------------
        partners = self.env['res.partner'].search_read(
            [('is_partner', '=', True)], ['name', 'current_balance', 'actual_balance'],
            order='current_balance desc', limit=8)
        partners_chart = {
            'labels': [p['name'] for p in partners],
            'current': [round(p['current_balance'] or 0.0, 2) for p in partners],
            'actual': [round(p['actual_balance'] or 0.0, 2) for p in partners],
        }

        # ---------------- installments ----------------
        inst_fields = ['name', 'due_date', 'amount', 'property_id', 'contact_id', 'is_purchased']
        open_installments = Installment.search_read(
            [('status', '=', 'draft')], inst_fields, order='due_date asc')
        in_30 = today + relativedelta(days=30)
        overdue = [i for i in open_installments if i['due_date'] and i['due_date'] < today]
        upcoming = [i for i in open_installments if i['due_date'] and today <= i['due_date'] <= in_30]

        def _inst_row(rec):
            return {
                'id': rec['id'], 'name': rec['name'],
                'due_date': fields.Date.to_string(rec['due_date']),
                'amount': rec['amount'] or 0.0,
                'property': rec['property_id'][1] if rec['property_id'] else '',
                'contact': rec['contact_id'][1] if rec['contact_id'] else '',
                'kind': 'purchase' if rec['is_purchased'] else 'sale',
            }

        installments = {
            'overdue_count': len(overdue),
            'overdue_receivable': round(sum(i['amount'] or 0.0 for i in overdue if not i['is_purchased']), 2),
            'overdue_payable': round(sum(i['amount'] or 0.0 for i in overdue if i['is_purchased']), 2),
            'upcoming_count': len(upcoming),
            'overdue': [_inst_row(i) for i in overdue[:6]],
            'upcoming': [_inst_row(i) for i in upcoming[:6]],
            'overdue_ids': [i['id'] for i in overdue],
        }

        # ---------------- latest transactions ----------------
        type_labels_tx = self._selection_labels('real.estate.transaction', 'transaction_type')
        latest = Transaction.search_read(
            [], ['name', 'partner_id', 'amount', 'transaction_type', 'transaction_date'],
            order='transaction_date desc, id desc', limit=6)
        latest_transactions = [{
            'id': t['id'], 'name': t['name'],
            'partner': t['partner_id'][1] if t['partner_id'] else '',
            'amount': t['amount'] or 0.0,
            'type': t['transaction_type'],
            'type_label': type_labels_tx.get(t['transaction_type'], t['transaction_type']),
            'date': fields.Date.to_string(t['transaction_date']),
        } for t in latest]

        return {
            'currency': {
                'symbol': currency.symbol, 'position': currency.position,
                'decimals': currency.decimal_places, 'name': currency.name,
            },
            'kpi': self._summary_kpis(),
            'status_chart': status_chart,
            'type_chart': type_chart,
            'area_chart': area_chart,
            'monthly': monthly,
            'category_chart': category_chart,
            'partners_chart': partners_chart,
            'installments': installments,
            'latest_transactions': latest_transactions,
            'alerts': {
                'ready_to_close': ready_to_close,
                'restructure_ready': restructure_ready,
                'incomplete_partnerships': incomplete_partnerships,
            },
            'generated_on': fields.Date.to_string(today),
        }
