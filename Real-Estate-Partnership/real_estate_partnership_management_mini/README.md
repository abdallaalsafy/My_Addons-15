# Real Estate Partnership Management Mini

An Odoo 15 application for managing real estate investments and the financial activity around them. It brings investment records, property purchases and sales, partner contributions, expenses, payment installments, cash movements, and management reports into one workspace.

## Purpose

The module helps a real estate business track each investment from acquisition through sale and closure. It provides a shared record of the properties and partners involved, monitors amounts due and paid, and gives managers financial summaries and reports for reviewing the business and its cash flow.

## Main capabilities

- **Investment tracking:** Create and monitor investments, their type, status, location, area, cost, and partnership allocation. Investment records can be reviewed alongside associated properties and expenses.
- **Property purchases and sales:** Maintain purchase and sale property records, their status, dates, prices, down payments, and payment schedules. Sale lines capture sale-related profit and management fee information.
- **Partner and contact records:** Classify contacts as partners, buyers, or sellers. Track partner balances and partnership participation, including partner payments and records related to partnership changes or exits where configured in the workflow.
- **Partnerships and contributions:** Record partners' participation in investments and the payments made against partnership commitments.
- **Installment follow-up:** Manage purchase and sale installments, record payment status and dates, and use the payment search wizard to filter payment records.
- **Expense management:** Record investment-level and company-level expenses, categorize them, link relevant investments or properties, record payment information, and attach supporting files.
- **Transactions and cash flow:** Record cash or bank movements and review a date-filtered cash flow ledger that combines transactions, paid expenses, property down payments, and paid installments.
- **Dashboard:** Review financial KPIs, investment and property charts, monthly purchases, sales, profits, expenses and cash movements, partner balances, upcoming or overdue installments, recent transactions, and investment alerts.
- **Reports:** Print property, investment, partnership, partner, unified partner ledger, company financial summary, and cash flow reports.
- **Cities and company options:** Maintain city records and configure company options for restricting sales when balance is low and automatically creating transactions by default.

## Application sections

The application menu currently exposes these main areas:

- **Dashboard** – operating and financial overview.
- **Contacts** – partners, buyers, sellers, and all contacts.
- **Investments** – investments, purchased properties, and sale properties.
- **Payments** – purchase installments, sale installments, and advanced payment search.

Expense, transaction, report, city, and company settings features are included in the module and may be opened through the relevant record actions or administrator configuration, depending on the installed menu configuration.

## Technical contents

| Directory | Contents |
| --- | --- |
| `models/` | City, company settings, dashboard data, expenses and categories, investments, partnerships and partnership payments, payment installments, properties, partner extensions, sale lines, and transactions. |
| `views/` | Forms, lists, search views, dashboard and application menus. |
| `wizards/` | Payment filtering, property payment receipts, partner unified ledger, cash flow ledger, and company financial summary assistants. |
| `reports/` | QWeb report definitions for operational and financial reports. |
| `security/` | User groups, record access definitions, and model access rights. |
| `data/` | Expense category defaults and numbering sequences. |
| `demo/` | Sample records for cities, partners, investments, properties, expenses, partnerships, payments, transactions, sales, and installments. |
| `static/` | Dashboard JavaScript, QWeb template, styles, and module icon. |
| `i18n/` | Arabic translations. |

## Requirements

- Odoo **15.0**
- Odoo modules: `base` and `mail`

## Installation

1. Place `real_estate_partnership_management_mini` in an Odoo addons path.
2. Restart the Odoo server and update the Apps list.
3. Install **Real Estate Partnership Management Mini** from the Apps menu.

The module manifest enables demo data. Odoo loads the bundled sample records when the database is installed with demo data enabled.

## Access and usage

The module defines Real Estate User and Real Estate Manager access groups. Users should be assigned the appropriate group by an administrator; managers receive elevated access to configuration and business records. Exact create, edit, delete, and reporting permissions vary by model.

A typical workflow is:

1. Set up cities, contacts, and company options.
2. Create an investment and register the purchased property or properties.
3. Define the partners' participation and register partnership payments.
4. Record investment or company expenses and track their payment status.
5. Create sale records for properties, then manage sale proceeds and purchase or sale installments.
6. Use the dashboard, ledgers, and reports to review balances, due payments, profitability, and cash movement.

## License and maintainer

- **License:** LGPL-3
- **Author:** Abdallaalsafy
- **Website:** [github.com/abdallaalsafy](https://github.com/abdallaalsafy)

## Notes

This module manages operational records and in-app financial summaries. The manifest lists only `base` and `mail` as dependencies; it does not declare integration with Odoo Accounting. Validate the module's business rules and reports against your organization's accounting and legal requirements before relying on them for statutory reporting.
