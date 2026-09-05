from odoo import models, fields, api


class Cls_search_cust_addr_of_mandoops(models.TransientModel):
    _name = 'wzrd_search_cust_addr_of_mandoops'
    _description = 'Wizard Of Search Custpomers And Address Of Mandoops'

    def fnc_get_domain(self):
        domain=[]
        mandoop = self.fld_mandoop_id
        collector = self.fld_collector_id
        collector_isall = self.fld_collector_isall_id
        paid = self.fld_is_paid
        modl = self.fld_model
        fld_mapped = ""

        if collector_isall:
            domain = [('fld_collector_isall_id','=',collector_isall.id)]
        if paid:
            if paid == 'yes':
                domain += [('fld_is_paid', '=', True)]
            elif paid == 'no':
                domain += [('fld_is_paid', '=', False)]
        if mandoop:
            domain += [('fld_mandoops.id','=',mandoop.id)]
        if collector:
            domain += [('fld_collector_id', '=', collector.id)]

        if domain:
            if modl == 'mdl_places':
                fld_mapped = 'fld_place_id'
            elif modl == 'mdl_regions':
                fld_mapped = 'fld_region_id'
            elif modl == 'mdl_customers':
                fld_mapped = 'fld_customer_id'

            lst_places_ids = self.env['mdl_isalls'].search(domain).mapped(fld_mapped).ids
            domain = [('id', 'in', lst_places_ids)]
        else:
            domain=[]
# ---------------------------------------
        return {'type': 'ir.actions.act_window',
            'name': 'Search Custpomers And Address Of Mandoops Form',
            'view_type': 'tree',
            'view_mode': 'list',
            'res_model': modl,
            'domain': domain}

    fld_mandoop_id = fields.Many2one('mdl_mandoops', string="Mandoop Name")
    fld_collector_id = fields.Many2one('mdl_mandoops', string="Collector Name")
    fld_collector_isall_id = fields.Many2one('mdl_mandoops', string="Collector_Isall Name")
    fld_is_paid = fields.Selection(selection=[('yes','Is Paid'),('no','Not Paid')], string="Sell_Qest Is Paid?")
    fld_model = fields.Selection(selection=[('mdl_places', 'Places'),
                                            ('mdl_regions', 'Regions'),
                                            ('mdl_customers', 'Customers')],
                                 string="The Model",
                                 required=True,
                                 default='mdl_places')