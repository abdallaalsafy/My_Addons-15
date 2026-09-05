from odoo import models, fields, api, _
from odoo.exceptions import UserError

class cls_catg_units(models.Model):
    _name = 'mdl_catg_units'
    _description = 'Table Of Categorys Units'
    _order = "name"
    _sql_constraints = [('UniqueCatgUnitName', 'unique (name)', 'The Name Of Category Is Existe Before')]


    name = fields.Char(string='Category', required=True)
    fld_description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    # related fields
    units_ids = fields.One2many('mdl_units', 'fld_catg_id', string='Units')
    # counted fields
    units_count = fields.Integer(compute='_compute_units_count', string='Units Count')


    # ===================== Built-in Functions ============================
    def unlink(self):
        # Check if any units in these categories are used before deletion
        all_unit_ids = self.mapped('units_ids').ids
        if all_unit_ids:
            # Use the units model to check usage
            units_model = self.env['mdl_units']
            is_used, usage_info = units_model.fnc_check_units_usage(all_unit_ids)
            
            if is_used:
                # Find which category contains this used unit
                used_category = self.filtered(lambda c: usage_info['unit_id'] in c.units_ids.ids)
                raise UserError(_('You Can Not Delete This Category %s Because Unit %s Is Used in %s' % 
                                 (used_category.name, usage_info['unit_name'], usage_info['model_name'])))
        
        return super(cls_catg_units, self).unlink()

    # ========================= Computed Functions =================================
    @api.depends('units_ids')
    def _compute_units_count(self):
        for catg in self:
            catg.units_count = len(catg.units_ids)