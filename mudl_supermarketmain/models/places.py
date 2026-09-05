from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_places(models.Model):
    _name = 'mdl_places'
    _description = 'Table Of All Places'
    _order = "fld_town_id, fld_street_id, name"

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    @api.onchange('fld_town_id')
    def fnc_town_changed(self):
        if (self.fld_town_id and self.fld_town_id != self.fld_street_id.fld_town_id) or not self.fld_town_id:
            self.fld_street_id = False

    @api.constrains('name', 'fld_street_id')
    def fnc_street_exist(self):
        obj2 = self.search(
            [('fld_street_id', '=', self.fld_street_id.id), ('name', '=', self.name), ('id', '!=', self.id)])
        if obj2:
            raise ValidationError(_('The Address Is Existing Before'))

    fld_town_id = fields.Many2one('mdl_towns', string='Town Name', required=True, ondelete="restrict")
    fld_street_id = fields.Many2one('mdl_streets', string='Street Name', required=True, ondelete="restrict", domain="[('fld_town_id', '=', fld_town_id)]")
    name = fields.Char(string='Name', required=True, index=True)
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')
