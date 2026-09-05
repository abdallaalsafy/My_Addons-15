# -*- coding: utf-8 -*-

from odoo import models, fields, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _sql_constraints = [('uniquefld_code', 'unique (fld_code)', 'The Code Is Existe Before')]


    fld_code = fields.Char(string="Product_Code",required=True)


class Partners(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [('unique_partner_fld_code', 'unique (fld_code)', 'The Code Is Existe Before')]

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            domain = ['|', ('name', operator, name),
                      ('fld_code', operator, name)]
            return self.search(domain + args, limit=limit).name_get()
        return super(Partners, self).name_search(name=name, args=args, operator=operator, limit=limit)


    fld_code = fields.Char(string="Partner_Code",required=True)