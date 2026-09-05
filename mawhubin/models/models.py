# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError

class mawhubin(models.Model):
    _name = 'mawhubin'
    _description = 'mawhubin'

    image = fields.Image(max_width=150, max_height=150, string="الصورة")
    name = fields.Char()
    date_birth = fields.Date(string="تاريخ الميلاد")
    adress = fields.Char(string="xxxx", copy=False)
    school = fields.Char()
    management = fields.Char(string="الادارة")
    national_id = fields.Char(size=14, string="الرقم القومي")
    phone_number = fields.Char(size=11, string="الهاتف")
    notes = fields.Text(string="ملاحظات")
    mawh2_ids=fields.One2many("mawhubin2","mawh1_id")


    def popupNotification(self):
        # self.env['bus.bus']._sendmany(self.env.user.partner_id,'simple_notification',{'title': 'My Title','message': 'My Message'})
        print(self.env['bus.bus'])

