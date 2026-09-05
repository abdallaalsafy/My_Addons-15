from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_zepoons(models.Model):
    _name = 'mdl_zepoons'
    _description = 'Table Of All Zepoons'
    _sql_constraints = [('unique_zepoons_name', 'unique (name)', 'The Name Is Existe Before')]

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    @api.onchange('fld_town_id')
    def fnc_town_changed(self):
        if (self.fld_town_id and self.fld_town_id != self.fld_street_id.fld_town_id) or not self.fld_town_id:
            self.fld_street_id = False

    @api.onchange('fld_street_id')
    def fnc_street_changed(self):
        if (self.fld_street_id and self.fld_street_id != self.fld_place_id.fld_street_id) or not self.fld_street_id:
            self.fld_place_id = False

    name = fields.Char(string='Name', required=True, index=True)
    fld_phone = fields.Text(string='Phone')
    fld_degree = fields.Char(string='Degree')
    fld_notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    fld_town_id = fields.Many2one('mdl_towns', string='Town Name', required=True, ondelete="restrict")
    fld_street_id = fields.Many2one('mdl_streets', string='Street Name', required=True, ondelete="restrict",
                                    domain="[('fld_town_id', '=', fld_town_id)]")
    fld_place_id = fields.Many2one('mdl_places', string='Place Name', required=True, ondelete="restrict",
                                   domain="[('fld_street_id', '=', fld_street_id)]")
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')
