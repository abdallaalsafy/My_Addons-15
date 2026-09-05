from odoo import models, fields, api, _
from odoo.exceptions import UserError


class cls_charges(models.Model):
    _name = 'mdl_charges'
    _description = 'Table Of All Charges'
    _order = "id desc"


    name = fields.Char(string="Code", default=lambda self: _('New'))
    fld_ref = fields.Char(string="Referance")
    fld_date = fields.Date(string='Date', required=True, )
    fld_notes = fields.Text(string='Notes')
    fld_store_f_id = fields.Many2one('mdl_stores', string="From Store",required=True,ondelete='restrict',domain="[('id','!=',fld_store_t_id)]")
    fld_store_t_id = fields.Many2one('mdl_stores', string="To Store",required=True,ondelete='restrict',domain="[('id','!=',fld_store_f_id)]")
    # related data
    fld_charges_goods_ids = fields.One2many('mdl_charges_goods', 'fld_charges_id', string="Goods")


    # ======================= Built-in Functions =======================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('chrg_sqnce')
        return super(cls_charges, self).create(vals_list)