from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    installment_line_ids = fields.One2many(
        'installment.line',
        'account_move_id',
        ondelete='cascade',
    )

    sales_type = fields.Selection(
        [('installment', 'Installment'),
         ('monetary', 'Monetary'), ],
        default='installment',
        string='Sales Type'
    )
    down_payment_type = fields.Selection(
        [('delayed', 'Delayed'),
         ('monetary', 'Monetary'),
         ],
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
        string="Date Of The First Installment",
        default=lambda self: fields.Date.today())

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
    def installment_lines(self):
        installment_line = []
        remainder = self.number_of_installments and (
                            self.amount_total - self.paid_or_offered) / self.number_of_installments
        for index in range(0, int(self.number_of_installments), 1):
            installment_vals = {
                'state': 'new',
                'due_date': self.date_of_the_first_installment and self.date_of_the_first_installment + relativedelta(
                    months=index),
                'amount': remainder,
                'type': 'installment',
                'reference': self.name,
                'customer_name': self.partner_id.name,
                'installment_name': 'Installment Number' + str(index + 1),
                'installment_line_number': index + 1,
                # 'paid_or_offered': self.paid_or_offered,
            }
            installment_line.append((0, 0, installment_vals))
        return installment_line

    @api.onchange('amount_total','invoice_line_ids','date_of_the_first_installment','number_of_installments')
    @api.constrains('date_of_the_first_installment')
    def _onchange_invoice_date(self):
        self.installment_line_ids=[(5,)]
        self.installment_line_ids=self.installment_lines()



