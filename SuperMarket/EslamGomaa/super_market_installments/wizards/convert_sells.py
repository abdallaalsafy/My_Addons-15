from odoo import models, fields, api, _

class cls_convert_sells(models.TransientModel):
    _name = 'wzrd_convert_sells'
    _description = 'Wizard Of Converting Sells'

    def fnc_convert_sells(self):
        is_qst = not self.fld_is_qst
        active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
        active_ids.write({'fld_is_qst':is_qst})

    def fnc_get_default(self):
        active_ids = self.env['mdl_sells'].browse(self._context.get('active_ids'))
        return active_ids[0].fld_is_qst

    fld_is_qst = fields.Boolean(string="Is Sells Qst?",default=fnc_get_default)
