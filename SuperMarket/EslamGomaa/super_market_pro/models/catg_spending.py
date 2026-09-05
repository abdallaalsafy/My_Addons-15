from odoo import models, fields, api, _

class cls_catg_spending(models.Model):
    _name = 'mdl_catg_spending'
    _description = 'Table Of Categorys Of Spending'
    _order = "id desc"
    _sql_constraints = [('UniqueCatgSpendingName', 'unique (name)', 'The Name Is Existe Before')]

    name = fields.Char(string="Name",required=True)
    fld_Desc = fields.Text(string="Description")