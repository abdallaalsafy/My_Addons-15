from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError


class InstallmentLine(models.Model):
    _name = 'installment.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Installment Lines"
    _rec_name = 'installment_name'
    _order = "installment_name, account_move_id, id"

    state = fields.Selection(
        [('paid', 'Paid'),
         ('new', 'New'),
         ],
        default='new',
        string='State'
    )
    due_date = fields.Date(
        string="Due Date",
        # store=True
    )
    amount = fields.Float(
        string="Amount"
    )
    type = fields.Selection(
        [('given', 'Given'),
         ('installment', 'Installment'),
         ],
        default='installment',
        string='Type'
    )
    reference = fields.Char(
        string="Reference"
    )
    customer_name = fields.Char(
        string="Customer Name"
    )
    installment_name = fields.Char(
        string="Installment Name"
    )
    account_move_id = fields.Many2one(
        'account.move',
        string="Account Move",
        ondelete='cascade',

    )
    region = fields.Many2one(
        'res.region',
        string="Region",
        related='account_move_id.region',
        store=True
    )
    sales_man = fields.Many2one(
        'hr.employee',
        string="Sales Man",
        related='account_move_id.sales_man',
        store=True

    )
    sales_person = fields.Many2one(
        'hr.employee',
        string="Sales Person",
        related='account_move_id.sales_person',
        store=True
    )
    phone = fields.Char(
        string="Customer Phone",
        size=11,
        default="01",
        related='account_move_id.phone',
        store=True
    )
    customer_address = fields.Char(
        string="Customer Address",
        related='account_move_id.customer_address',
        store=True
    )
    national_id = fields.Char(
        string="National ID",
        size=14,
        related='account_move_id.national_id',
        store=True
    )
    installment_line_number = fields.Integer(
        string="Number"
    )
    paid_or_offered = fields.Integer(
        string="Paid Or Offered",
    )
    is_print = fields.Boolean(
        readonly=True
    )

    def set_to_paid(self):
        record = self.env['installment.line'].search(
            [('due_date', '=', datetime.date(datetime.today()))])
        for rec in record:
            rec.state = 'paid'

    def print_report(self):
        for rec in self:
            if rec.is_print:
                raise ValidationError(_("Your are not allowed to print this installment again!"))
            else:
                for id in self.ids:
                    self._cr.execute("""
                    update installment_line set is_print=True WHERE id = %s
                    """%(id))
                return self.env.ref('sales_and_invoice_system.real_state_invoice_report_id').report_action(self, data={})

    def delete_installment_lines_automatic(self):
        records=self.env['installment.line'].search([('is_print','=',True)])
        for rec in records:
            rec.unlink()