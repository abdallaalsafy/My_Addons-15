from odoo import models, fields, api


class HmsDepartment(models.Model):
    _name = "hms.department"

    name = fields.Char(string="Name")
    capacity = fields.Integer(string="Capacity")
    is_opened = fields.Boolean(string="IS Opened?")
    patients_ids = fields.One2many(comodel_name="hms.patient",
                                   inverse_name="department_id",
                                   string="Patients")