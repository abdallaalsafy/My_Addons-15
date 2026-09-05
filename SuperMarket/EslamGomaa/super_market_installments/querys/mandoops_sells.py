from odoo import models, fields, api, _

class cls_mandoops_sells(models.Model):
    _name = 'mdl_mandoops_sells'
    _auto = False
    _description = 'Table Of Mandoops Sells'
    _order = "mdl_mandoops_id"

    mdl_mandoops_id = fields.Many2one("mdl_mandoops", string="Mandoop")
    fld_total_qst = fields.Float(string='Total Qest')
    fld_count_sells=fields.Integer(string="Count Sells")
    fld_count_cash = fields.Integer(string="Count Cash")
    fld_count_qst = fields.Integer(string="Count Qest")

    fld_count_sells_r = fields.Integer(string="Count Return Sells")
    fld_count_cash_r = fields.Integer(string="Count Return Cash")
    fld_count_qst_r = fields.Integer(string="Count Return Qest")

    fld_win_qst = fields.Float(string='Winning Qest')
    fld_total_hafez = fields.Float(string='Total Hafez')

    fld_total = fields.Float(string='Total Cash')
    fld_win = fields.Float(string='Winning Cash')

    fld_total_sells = fields.Float(string='Total Sells')
    fld_total_winning = fields.Float(string='Total Winning')