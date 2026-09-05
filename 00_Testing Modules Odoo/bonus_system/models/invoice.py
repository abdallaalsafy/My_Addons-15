from odoo import api, fields, models, _


class Invoice(models.Model):
    _inherit = 'account.move'

    employee_ids = fields.Many2many(
        'hr.employee',
        string="Representatives"
    )
    bonus_per_employee = fields.Float(
        string="Bonus",
        compute='_compute_bonus_per_employee'
    )

    @api.depends('employee_ids', 'invoice_line_ids')
    def _compute_bonus_per_employee(self):
        for rec in self:
            total_bonus = sum(rec.invoice_line_ids.mapped('bonus'))
            if rec.employee_ids:
                rec.bonus_per_employee = total_bonus / len(rec.employee_ids)
            else:
                rec.bonus_per_employee = 0.0


class InvoiceLine(models.Model):
    """
        Inherit Account Move:
    """
    _inherit = 'account.move.line'

    bonus = fields.Float(
        string="Bonus",
        related='product_id.bonus'
    )
