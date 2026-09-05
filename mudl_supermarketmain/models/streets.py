from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.public_class import MainClass


class cls_streets(models.Model):
    _name = 'mdl_streets'
    _description = 'Table Of All Streets'

    @api.onchange('name')
    def fnc_editstring(self): self.name = MainClass().fnc_editstring(self.name)

    @api.constrains('name', 'fld_town_id')
    def fnc_street_exist(self):
        obj2 = self.search(
            [('fld_town_id', '=', self.fld_town_id.id), ('name', '=', self.name), ('id', '!=', self.id)])
        if obj2:
            raise ValidationError(_('The Street Is Existing Before'))

    name = fields.Char(string='Name', required=True, index=True)
    fld_town_id = fields.Many2one('mdl_towns', string='Town Name', required=True, ondelete="restrict")
