from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    related_patient_id = fields.Many2one(comodel_name="hms.patient",
                                    string="Patient")

    @api.constrains("email")
    def constrains_email(self):
        email = self.email
        if email:
            patient_email_lst= self.env['hms.patient'].search([('email','=',email)])
            if patient_email_lst:
                raise ValidationError(_("The Email Is exite Before In Patient Model"))

    def unlink(self):
        has_group = self.user_has_groups('hms.unlink_partner_group_id')
        print(has_group)
        for obj in self:
            if obj.related_patient_id and has_group:
                raise ValidationError(_('You cont Delete This Record Becouse It Has Patient'))
        rtn = super(ResPartner, self).unlink()
        return rtn