from odoo import models, fields, api, _
from odoo.exceptions import UserError


class cls_units(models.Model):
    _name = 'mdl_units'
    _description = 'Table Of Goods Units'
    _order = "fld_catg_id,fld_factor"
    _sql_constraints = [('UniqueUnitName', 'unique (name)', 'The Name Of Unit Is Existe Before'),
                        ('ChkUnitFactorZero', 'Check (fld_factor>0)', 'The Ratio For Unit Must Be Above Zero!'),
                        ('ChkUnitRefFactorIsOne', "Check ((fld_type = 'ref' AND fld_factor = 1.0) OR (fld_type != 'ref'))", "The Factor Of Reference Unit Must Equal To 1.")]



    name = fields.Char(string='Unit Name', required=True)
    fld_catg_id = fields.Many2one('mdl_catg_units', 'Category Unit', required=True, ondelete='cascade')
    fld_factor = fields.Float(string='Factor Unit', default=1.0, compute='_compute_factor', store=True)
    fld_ratio = fields.Float(string='Ratio Unit', default=1.0, required=True)
    fld_type = fields.Selection([
        ('big', 'Bigger Than Reference'),
        ('ref', 'Reference'),
        ('smll', 'Smaller Than Reference')], string='Unit Type',default='ref', required=True)
    fld_description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color', compute='_compute_color')


    # ===================== Built-in Functions ============================
    @api.model_create_multi
    def create(self, vals_list):
        res = super(cls_units, self).create(vals_list)
        res.fnc_chk_ref_is_one()
        return res

    def write(self, values):
        # Check if trying to change category of reference unit
        new_catg = values.get('fld_catg_id')
        if new_catg and new_catg != self.fld_catg_id and self.fld_type == 'ref':
            raise UserError(_("You Cannot Update Reference Unit Category."))
        
        # Check if unit is used before changing ratio or category
        changing_ratio_or_catg = ('fld_ratio' in values and values['fld_ratio'] != self.fld_ratio) or \
                               ('fld_catg_id' in values and values['fld_catg_id'] != self.fld_catg_id.id)
        
        if changing_ratio_or_catg:
            is_used, usage_info = self.fnc_check_units_usage([self.id])
            if is_used:
                raise UserError(_("Unit '%s' Is Used Before, You Cannot Update Its Ratio Or Category.") % self.name)
        
        # Apply changes
        res = super(cls_units, self).write(values)
        
        # Validate reference units after changes
        self.fnc_chk_ref_is_one()
        return res

    def unlink(self):
        # Check if any units are reference units
        ref_units = self.filtered(lambda u: u.fld_type == 'ref')
        if ref_units:
            raise UserError(_('You Cannot Delete Reference Unit(s): %s') % ', '.join(ref_units.mapped('name')))
        
        return super(cls_units, self).unlink()

    # ========================= Computed Functions =================================
    @api.depends('fld_type', 'fld_ratio')
    def _compute_factor(self):
        """Compute the factor based on unit type and ratio"""
        for unit in self:
            if not unit.fld_type or unit.fld_ratio <= 0:
                unit.fld_factor = 1
                continue
                
            if unit.fld_type == 'ref':
                # Reference units always have factor = 1
                unit.fld_factor = 1
            elif unit.fld_type == 'big':
                # Bigger units: 1 / ratio (e.g., 1 dozen = 1/12 units)
                unit.fld_factor = 1 / unit.fld_ratio
            else:  # 'smll'
                # Smaller units: ratio (e.g., 1 meter = 100 cm)
                unit.fld_factor = unit.fld_ratio

    @api.depends('fld_type')
    def _compute_color(self):
        for unt in self:
            if unt.fld_type == 'ref':
                unt.color = 7
            else:
                unt.color = 0

    # ============================== Custom Functions =============================
    def fnc_chk_ref_is_one(self):
        """Check if a category has exactly one reference unit"""
        # Get unique categories to check
        categories = self.mapped('fld_catg_id')
        for catg in categories:
            # Count reference units in this category
            ref_units = catg.units_ids.filtered(lambda u: u.fld_type == 'ref')
            if len(ref_units) > 1:
                raise UserError(_("Category '%s' Should Only Have One Reference Unit. Found: %s") % 
                               (catg.name, ', '.join(ref_units.mapped('name'))))
            elif len(ref_units) == 0:
                raise UserError(_("Category '%s' Should Have a Reference Unit.") % catg.name)

    def fnc_check_units_usage(self, unit_ids):
        """Check if any units are used in related models"""
        if not unit_ids:
            return False, None
            
        models_to_check = [
            'mdl_goods',
            'mdl_buys_goods', 
            'mdl_buys_r_goods',
            'mdl_sells_goods',
            'mdl_sells_r_goods',
            'mdl_charges_goods'
        ]
        
        for model_name in models_to_check:
            try:
                model = self.env[model_name]
                used_records = model.search([('fld_unit_id', 'in', unit_ids)], limit=1)
                if used_records:
                    return True, {
                        'unit_id': used_records.fld_unit_id.id,
                        'unit_name': used_records.fld_unit_id.name,
                        'model_name': model_name
                    }
            except KeyError:
                continue
        
        return False, None
