from odoo import models, fields, api


class Cls_received_isalls(models.TransientModel):
    _name = 'wzrd_received_isalls'
    _description = 'Wizard Of Received Isalls'

    def fnc_set_collctr_isal(self):
        collctr = self.fld_collctr_isal_id
        active_ids = self.env['mdl_isalls'].browse(self._context.get('active_ids'))
        if collctr:
            active_ids.write({'fld_collctr_isal_id': collctr})

    fld_collctr_isal_id = fields.Many2one('mdl_mandoops', string="Collector Isal", required=True)