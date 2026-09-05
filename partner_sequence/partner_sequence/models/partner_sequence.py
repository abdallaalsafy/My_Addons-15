from odoo import models, fields, api,_

class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        vals['fld_seq'] = self.env['ir.sequence'].next_by_code('partner_sqnce')
        return super(Partner, self).create(vals)

    fld_seq= fields.Char(string="Code", default=lambda self: _('New'))

