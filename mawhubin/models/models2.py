# -*- coding: utf-8 -*-

from odoo import models, fields, api,registry,tools
from datetime import date

class mawhubin2(models.Model):
    _name = 'mawhubin2'
    _description = 'mawhubin2'


    name = fields.Char(default="dddddd")
    mawh1_id=fields.Many2one('mawhubin')
    country_id = fields.Many2one('mdl_country')
    phone_number = fields.Char()
    number = fields.Integer()
    brthdate=fields.Date()
    age=fields.Integer(string="AAAAggggeee")
    lang = fields.Integer()
    xlang = fields.Selection(lambda self:self.env['res.lang'].get_installed(), default=lambda self: self.env.lang)
    slction = fields.Selection([('6', 'Type 2'),('4', 'Type 1') ])
    state = fields.Selection([('draft', 'Draft'), ('progress', 'Progress')])


