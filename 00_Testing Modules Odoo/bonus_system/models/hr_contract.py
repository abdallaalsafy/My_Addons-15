from odoo import api, fields, models, _


class HrContract(models.Model):
    """
        Inherit Hr Contract:
    """
    _inherit = 'hr.contract'

    representative_bonus = fields.Float(
        string="Representative Bonus",
        compute='_compute_bonus',
    )
    return_bonus = fields.Float(
        string="Return Bonus",
        compute='_compute_bonus',
    )

    @api.depends('employee_id', 'state')
    def _compute_bonus(self):
        bonus = 0.0
        return_bonus = 0.0
        posted_record = self.env['account.move'].search(
            [('state', '=', 'posted')])
        cancel_record = self.env['account.move'].search(
            [('state', '=', 'cancel')])
        for obj in self:
            for post_rec in posted_record:
                if post_rec and obj.employee_id in post_rec.employee_ids:
                    bonus += post_rec.bonus_per_employee
            for cancel_rec in cancel_record:
                if obj.employee_id in cancel_rec.employee_ids and cancel_rec:
                    return_bonus += cancel_rec.bonus_per_employee
            if obj.state == 'open':
                obj.representative_bonus = bonus
                obj.return_bonus = return_bonus
            else:
                obj.representative_bonus = 0.0
                obj.return_bonus = 0.0
