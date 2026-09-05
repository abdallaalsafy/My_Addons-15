from odoo import api, fields, models, _
from dateutil import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_type = fields.Selection(
        [('installment', 'Installment'),
         ('monetary', 'Monetary'), ],
        default='installment',
        string='Sales Type'
    )
    down_payment_type = fields.Selection(
        [('delayed', 'Delayed'),
         ('monetary', 'Monetary'), ],
        default='monetary',
        string='Down Payment Type'
    )
    region = fields.Many2one(
        'res.region',
        string="Region",
    )
    number_of_installments = fields.Integer(
        string="Number Of Installments"
    )
    date_of_the_first_installment = fields.Date(
        string="Date Of The First Installment"
    )
    phone = fields.Char(
        string="Customer Phone",
        size=11,
        default="01"
    )
    customer_address = fields.Char(
        string="Customer Address"
    )
    national_id = fields.Char(
        string="National ID",
        size=14,
    )
    paid_or_offered = fields.Integer(
        string="Paid Or Offered",
    )
    sales_man = fields.Many2one(
        'hr.employee',
        string="Sales Man"
    )
    sales_person = fields.Many2one(
        'hr.employee',
        string="Sales Person"
    )

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for invoice in self.invoice_ids:
            invoice.button_cancel()
            invoice.installment_line_ids.unlink()
        # for picking in self.picking_ids:
        # if picking.state == 'done':
        # for rec in self.env['stock.return.picking'].search(
        #             [('picking_id', 'in', self.picking_ids.ids)]):
        #     rec.create_returns()
        return res

    #
    def installment_lines(self):
        installment_line = []
        if self.down_payment_type == "monetary":
            monetary_value = {
                'state': 'paid',
                'due_date': str(self.date_order),
                'amount': self.paid_or_offered,
                'type': 'given',
                'reference': self.name,
                'customer_name': self.partner_id.name,
                'installment_name': 'Down Payment'
            }
            installment_line.append((0, 0, monetary_value))
        else:
            pass
        remainder = (
                            self.amount_total - self.paid_or_offered) / self.number_of_installments
        for index in range(0, int(self.number_of_installments), 1):
            installment_vals = {
                'state': 'new',
                'due_date': self.date_of_the_first_installment + relativedelta.relativedelta(
                    months=index + 1),
                'amount': remainder,
                'type': 'installment',
                'reference': self.name,
                'customer_name': self.partner_id.name,
                'installment_name': 'Installment Number' + str(index + 1),
                'installment_line_number': index + 1,
                'paid_or_offered': self.paid_or_offered,
            }
            installment_line.append((0, 0, installment_vals))
        return installment_line

    def invoice_lines(self):
        invoice_lines = []
        for line in self.order_line:
            vals = {
                'name': line.name,
                'price_unit': line.price_unit,
                'quantity': line.product_uom_qty,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'tax_ids': [(6, 0, line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [line.id])],
            }
            invoice_lines.append((0, 0, vals))
        return invoice_lines

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for picking in self.picking_ids:
            if picking.state == "assigned":
                picking.action_set_quantities_to_reservation()
                picking.button_validate()
            else:
                pass
        self.env['account.move'].create({
            'ref': self.client_order_ref,
            'move_type': 'out_invoice',
            'sales_type': self.sales_type,
            'region': self.region.id,
            'down_payment_type': self.down_payment_type,
            'number_of_installments': self.number_of_installments,
            'invoice_origin': self.name,
            'phone': self.phone,
            'national_id': self.national_id,
            'paid_or_offered': self.paid_or_offered,
            'sales_man': self.sales_man or False,
            'sales_person': self.sales_person or False,
            'customer_address': self.customer_address or False,
            'date_of_the_first_installment': self.date_of_the_first_installment or False,
            'invoice_user_id': self.user_id.id,
            'partner_id': self.partner_invoice_id.id,
            'currency_id': self.pricelist_id.currency_id.id,
            'invoice_line_ids':self.invoice_lines(),
            'installment_line_ids': self.installment_lines() if self.sales_type == 'installment' else False,
            'employee_ids': [
                                (6, 0, [
                                    self.sales_man.id if self.sales_person else False,
                                    self.sales_person.id if self.sales_person else False, ])] and self.sales_person or self.sales_man
        }).write({'state': 'posted'})
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ratio = fields.Float(
        string="Ratio",
    )
