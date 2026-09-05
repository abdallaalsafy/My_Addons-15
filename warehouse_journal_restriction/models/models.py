from odoo import models, fields, api,_

class Users(models.Model):
    _inherit = 'res.users'
    warehouse_operation_ids = fields.Many2many(comodel_name='stock.picking.type', string='Restricted Warehouses Operations')
    journal_ids = fields.Many2many(comodel_name='account.journal', string='Restricted Journals')

