/** @odoo-module **/

// Odoo 15 version: OWL 1.x (global `owl`), no "@odoo/owl" import, no Chart.js helper from core.

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

const { Component } = owl;
const { useRef, useState } = owl.hooks;

const PALETTE = ["#714B67", "#2a9d8f", "#e07b39", "#3d6fb6", "#d9534f", "#8a5cc2", "#f0ad4e", "#6c757d"];
const CHART_URLS = ["/web/static/lib/Chart/Chart.js", "/web/static/lib/Chart/Chart.min.js"];

function tr(text) {
    return typeof _t === "function" ? _t(text) : text;
}

function loadScript(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = url;
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Cannot load " + url));
        document.head.appendChild(script);
    });
}

async function ensureChartLibrary() {
    if (window.Chart) {
        return true;
    }
    for (const url of CHART_URLS) {
        try {
            await loadScript(url);
            if (window.Chart) {
                return true;
            }
        } catch (error) {
            // try the next location
        }
    }
    return false;
}

function userLang() {
    try {
        const info = (typeof odoo !== "undefined" && odoo.session_info) || {};
        const lang = (info.user_context && info.user_context.lang) || document.documentElement.lang || "en_US";
        return String(lang).replace("_", "-");
    } catch (error) {
        return "en-US";
    }
}

export class RealEstateDashboard extends Component {
    constructor() {
        super(...arguments);
        
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.state = useState({ loading: true, data: null });
        this.charts = {};
        this.needsRender = false;
        this.lang = userLang();
        this.refs = {
            trade: useRef("chart_trade"),
            profit: useRef("chart_profit"),
            cash: useRef("chart_cash"),
            category: useRef("chart_category"),
            status: useRef("chart_status"),
            type: useRef("chart_type"),
            area: useRef("chart_area"),
            partners: useRef("chart_partners"),
        };
    }

    // ------------------------------------------------------------------
    // OWL 1 lifecycle
    // ------------------------------------------------------------------
    async willStart() {
        await ensureChartLibrary();
        await this.load();
    }

    mounted() {
        this.renderCharts();
    }

    patched() {
        if (this.needsRender) {
            this.needsRender = false;
            this.renderCharts();
        }
    }

    willUnmount() {
        this.destroyCharts();
    }

    // ------------------------------------------------------------------
    // data
    // ------------------------------------------------------------------
    async load() {
        this.needsRender = false;
        this.state.loading = true;
        const data = await this.rpc("/web/dataset/call_kw/real.estate.dashboard/get_dashboard_data", {
            model: "real.estate.dashboard",
            method: "get_dashboard_data",
            args: [],
            kwargs: {},
        });
        this.state.data = data;
        this.state.loading = false;
        this.needsRender = true;
    }

    async refresh() {
        await this.load();
    }

    // ------------------------------------------------------------------
    // formatting helpers
    // ------------------------------------------------------------------
    fmt(value, decimals) {
        const places = decimals || 0;
        const cur = this.state.data.currency;
        const number = Number(value || 0).toLocaleString("en-US", {
            minimumFractionDigits: places,
            maximumFractionDigits: places,
        });
        return cur.position === "before" ? cur.symbol + " " + number : number + " " + cur.symbol;
    }

    count(value) {
        return Number(value || 0).toLocaleString("en-US");
    }

    monthLabels() {
        return this.state.data.monthly.months.map((key) => {
            const parts = key.split("-");
            return new Date(Number(parts[0]), Number(parts[1]) - 1, 1).toLocaleDateString(this.lang, {
                month: "short",
                year: "2-digit",
            });
        });
    }

    // ------------------------------------------------------------------
    // KPI cards and alerts
    // ------------------------------------------------------------------
    get cards() {
        const k = this.state.data.kpi;
        const inst = this.state.data.installments;
        return [
            {
                key: "liquidity", color: PALETTE[1], label: tr("Actual Liquidity"),
                value: this.fmt(k.actual_liquidity),
                sub: [tr("Deposits") + ": " + this.fmt(k.positive_transactions), tr("Withdrawals") + ": " + this.fmt(k.negative_transactions)],
            },
            {
                key: "investments", color: PALETTE[0], label: tr("Open Investments"),
                value: this.count(k.investments_open_count),
                sub: [tr("Total investments") + ": " + this.count(k.investments_count), tr("Open amount") + ": " + this.fmt(k.investments_open_amount)],
            },
            {
                key: "partners", color: PALETTE[3], label: tr("Partners Balance"),
                value: this.fmt(k.partners_current_balance),
                sub: [tr("Active partners") + ": " + this.count(k.partners_active_count), tr("Debtor partners") + ": " + this.count(k.partners_debtor_count)],
            },
            {
                key: "purchases", color: PALETTE[2], label: tr("Purchases"),
                value: this.fmt(k.purchases_total_price),
                sub: [tr("Count") + ": " + this.count(k.purchases_count), tr("Unpaid") + ": " + this.fmt(k.purchases_unpaid_amount)],
            },
            {
                key: "sales", color: PALETTE[4], label: tr("Sales"),
                value: this.fmt(k.sales_total_price),
                sub: [tr("Count") + ": " + this.count(k.sales_count), tr("Unpaid") + ": " + this.fmt(k.sales_unpaid_amount)],
            },
            {
                key: "profit", color: PALETTE[5], label: tr("Net Profit"),
                value: this.fmt(k.sales_total_net_profit),
                sub: [tr("Total profit") + ": " + this.fmt(k.sales_total_profit), tr("Management fees") + ": " + this.fmt(k.sales_total_management_fees)],
            },
            {
                key: "expenses", color: PALETTE[6], label: tr("Expenses"),
                value: this.fmt(k.expenses_total_amount),
                sub: [tr("Investments") + ": " + this.fmt(k.expenses_investment_amount), tr("Company") + ": " + this.fmt(k.expenses_company_amount)],
            },
            {
                key: "overdue", color: PALETTE[7], label: tr("Overdue Installments"),
                value: this.count(inst.overdue_count),
                sub: [tr("To collect") + ": " + this.fmt(inst.overdue_receivable), tr("To pay") + ": " + this.fmt(inst.overdue_payable)],
            },
        ];
    }

    get alerts() {
        const a = this.state.data.alerts;
        const inst = this.state.data.installments;
        return [
            { key: "ready_to_close", label: tr("Investments ready to close"), ids: a.ready_to_close, model: "real.estate.investment" },
            { key: "restructure_ready", label: tr("Ready for restructuring"), ids: a.restructure_ready, model: "real.estate.investment" },
            { key: "incomplete_partnerships", label: tr("Partnerships below 100%"), ids: a.incomplete_partnerships, model: "real.estate.investment" },
            { key: "overdue_installments", label: tr("Overdue installments"), ids: inst.overdue_ids, model: "real.estate.payment.installment" },
        ];
    }

    // ------------------------------------------------------------------
    // navigation
    // ------------------------------------------------------------------
    openList(name, model, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: model,
            views: [[false, "list"], [false, "form"]],
            domain: domain || [],
            target: "current",
        });
    }

    openCard(ev) {
        const key = ev.currentTarget.dataset.key;
        const map = {
            investments: [tr("Investments"), "real.estate.investment", [["status", "=", "opening"]]],
            partners: [tr("Partners"), "res.partner", [["is_partner", "=", true]]],
            purchases: [tr("Purchase Properties"), "real.estate.property", [["is_purchased", "=", true]]],
            sales: [tr("Sale Properties"), "real.estate.property", [["is_purchased", "=", false]]],
            expenses: [tr("Expenses"), "real.estate.expense", []],
            overdue: [tr("Overdue installments"), "real.estate.payment.installment", [["id", "in", this.state.data.installments.overdue_ids]]],
        };
        if (map[key]) {
            this.openList(map[key][0], map[key][1], map[key][2]);
        }
    }

    openAlert(ev) {
        const key = ev.currentTarget.dataset.key;
        const alert = this.alerts.find((a) => a.key === key);
        if (alert && alert.ids.length) {
            this.openList(alert.label, alert.model, [["id", "in", alert.ids]]);
        }
    }

    openRecord(ev) {
        const dataset = ev.currentTarget.dataset;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: dataset.model,
            res_id: Number(dataset.id),
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ------------------------------------------------------------------
    // charts (Chart.js 2.x compatible: defaults only)
    // ------------------------------------------------------------------
    destroyCharts() {
        Object.keys(this.charts).forEach((name) => this.charts[name].destroy());
        this.charts = {};
    }

    makeChart(name, type, labels, datasets) {
        const ref = this.refs[name];
        if (!ref || !ref.el || !window.Chart) {
            return;
        }
        if (this.charts[name]) {
            this.charts[name].destroy();
        }
        this.charts[name] = new window.Chart(ref.el.getContext("2d"), {
            type: type,
            data: { labels: labels, datasets: datasets },
            options: { responsive: true, maintainAspectRatio: false },
        });
    }

    solid(label, data, color) {
        return { label: label, data: data, backgroundColor: color, borderColor: color };
    }

    renderCharts() {
        if (!this.state.data || !window.Chart) {
            return;
        }
        const d = this.state.data;
        const months = this.monthLabels();
        this.makeChart("trade", "bar", months, [
            this.solid(tr("Purchases"), d.monthly.purchases, PALETTE[2]),
            this.solid(tr("Sales"), d.monthly.sales, PALETTE[1]),
        ]);
        this.makeChart("profit", "line", months, [
            { label: tr("Net profit"), data: d.monthly.profits, borderColor: PALETTE[1], backgroundColor: PALETTE[1], fill: false },
            { label: tr("Expenses"), data: d.monthly.expenses, borderColor: PALETTE[4], backgroundColor: PALETTE[4], fill: false },
        ]);
        this.makeChart("cash", "bar", months, [
            this.solid(tr("Deposits"), d.monthly.deposits, PALETTE[3]),
            this.solid(tr("Withdrawals"), d.monthly.withdrawals, PALETTE[4]),
        ]);
        this.makeChart("category", "doughnut", d.category_chart.labels, [
            { data: d.category_chart.values, backgroundColor: PALETTE },
        ]);
        this.makeChart("status", "doughnut", d.status_chart.labels, [
            { data: d.status_chart.values, backgroundColor: PALETTE },
        ]);
        this.makeChart("type", "doughnut", d.type_chart.labels, [
            { data: d.type_chart.values, backgroundColor: PALETTE },
        ]);
        this.makeChart("area", "bar", d.area_chart.labels, [
            this.solid(tr("Sold area"), d.area_chart.sold, PALETTE[1]),
            this.solid(tr("Remaining area"), d.area_chart.remaining, PALETTE[2]),
        ]);
        this.makeChart("partners", "bar", d.partners_chart.labels, [
            this.solid(tr("Current balance"), d.partners_chart.current, PALETTE[0]),
            this.solid(tr("Actual balance"), d.partners_chart.actual, PALETTE[3]),
        ]);
    }
}

RealEstateDashboard.template = "real_estate_partnership_management_mini.Dashboard";

registry.category("actions").add("real_estate_dashboard", RealEstateDashboard);