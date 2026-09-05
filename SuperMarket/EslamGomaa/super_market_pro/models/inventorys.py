from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..mine_3 import cls_sqls


class cls_inventorys(models.Model):
    _name = 'mdl_inventorys'
    _description = 'Table Of All Inventorys'
    _order = "id desc"


    name = fields.Char(string="Code", default=lambda self: _('New'))
    fld_date = fields.Datetime(string='Date', default=fields.Datetime.now(), readonly=True)
    fld_notes = fields.Text(string='Notes')
    fld_store_id = fields.Many2one('mdl_stores', string="Store", required=True, ondelete='restrict')
    fld_inventory_goods_ids = fields.One2many('mdl_inventorys_goods', 'fld_inventory_id', store=True,
                                              compute='_compute_inventory_goods_ids',string="Inventory Goods", readonly=True)

    # ======================= Built-in Functions =======================
    @api.model_create_multi
    def create(self, vals_list):
        """Create inventory records with sequence and timestamp"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('inv_sqnce')
            vals['fld_date'] = fields.Datetime.now()
        return super(cls_inventorys, self).create(vals_list)

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.fld_store_id:
                name = f"{record.name} - {record.fld_store_id.name}"
            result.append((record.id, name))
        return result

    # ======================= Onchange Functions =======================
    @api.depends('fld_store_id')
    def _compute_inventory_goods_ids(self):
        """Load goods from selected store for inventory"""
        self.fld_inventory_goods_ids = [(5,)]  # Clear existing records
        
        if self.fld_store_id:
            store_id = self.fld_store_id.id
            inventory_goods_ids = []
            # Get all goods that exist in this store using SQL helper
            goods_fetch = cls_sqls().fnc_get_count_goods_in_one_store(self, store_id)
            ids = [item["fld_goods_id"] for item in goods_fetch]
            goods_records = self.env['mdl_goods'].browse(ids)

            records_map = {rec.id: rec for rec in goods_records}

            for item in goods_fetch:
                record = records_map.get(item['fld_goods_id'])

                if record:
                    item['fld_count'] *= record.fld_unit_id.fld_factor
                    inventory_goods_ids.append((0, 0, item))
            
            self.fld_inventory_goods_ids = inventory_goods_ids