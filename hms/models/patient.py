from odoo import models, fields, api, _
from bs4 import BeautifulSoup
from odoo.exceptions import ValidationError
import datetime
import re

class HmsPatient(models.Model):
    _name = "hms.patient"

    name = fields.Char(string="First Name", required=True)
    last_name = fields.Char(string="Last Name", required=True)
    birth_date = fields.Date(string="Birth Date")
    history = fields.Html(string="History")
    cr_ratio = fields.Float(string="CR Ratio")
    blood_type = fields.Selection(selection=[("a","A"), ("b","B"), ("o","O")], string="Boold Type")
    pcr = fields.Boolean(string="PCR")
    img = fields.Image(max_width=100, max_height=100)
    address = fields.Text(string="Address")
    age = fields.Integer(string="Age", compute='_compute_age', store=True)
    email = fields.Char(string="Email")
    department_id = fields.Many2one(comodel_name="hms.department",
                                    string="Department",
                                    domain=[("is_opened","=",True)])
    capacity = fields.Integer(related="department_id.capacity",
                              string="Capacity")
    doctor_ids = fields.Many2many(comodel_name="hms.doctor",
                                    string="Doctors")
    state = fields.Selection(selection=[("undetermined", "Undetermined"),
                                        ("good", "Good"),
                                        ("fair", "Fair"),
                                        ("serious", "Serious")],
                             string="State")

    _sql_constraints = [('UniqueEmail', 'unique (email)', 'The email Is Existe Before')]

    @api.constrains("email")
    def constrains_email(self):
        email = self.email
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+[̇a-zA-Z0-9-.]+'
        if email and not re.match(pattern, email):
            raise ValidationError (_("The Email Is Not Vaild"))

    @api.depends('birth_date')
    def _compute_age(self):
        for rec in self:
            if rec.birth_date:
                rec.age = datetime.datetime.now().year-rec.birth_date.year
            else:
                rec.age = 0

    @api.onchange("state")
    def on_change_state(self):
        basic_row = f"""
        <table class="table table-bordered">
            <thead><tr>
                <th>User</th>
                <th>Date</th>
                <th>Inf</th>
            </tr></thead>
            <tbody></tbody>
        </table>
        """

        soup = BeautifulSoup(self.history or "", "html.parser")
        tbody = soup.find("tbody")
        if tbody:
            add_row = soup.new_tag("tr")

            td_created_by = soup.new_tag("td")
            td_created_by.string = self.env.user.name
            add_row.append(td_created_by)

            td_date = soup.new_tag("td")
            td_date.string = str(fields.Date.today())
            add_row.append(td_date)

            td_description = soup.new_tag("td")
            td_description.string = self.state
            add_row.append(td_description)

            tbody.append(add_row)
            self.history = str(soup)
        else:
            self.history = basic_row

    @api.onchange("age")
    def on_change_age(self):
        age = self.age
        if age and age<30:
            self.pcr = True
            return {'warning': {'title': _('Warning!'),'message': _("PCR Field Is Checked"),'type': 'notification'}}
        return