from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..mine_3 import cls_sqls

class cls_update_goods(models.TransientModel):
    _name = 'wzrd_update_goods'
    _description = 'Wizard Of Update goods'


    fld_category_id = fields.Many2one('mdl_categorys', string=_("Category"))
    fld_unit_id = fields.Many2one("mdl_units", string=_('Unit'))
    fld_alarms = fields.Integer(string=_('Alarms'))
    fld_notes = fields.Text(string=_('Notes'))

    fld_buy_update = fields.Selection([('ratio', _('Ratio')), ('sum', _('Sum'))], string=_("Buy Update Type"))
    fld_buy_ratio = fields.Float(
        string=_("Buy Ratio (%)"),help=_("Percentage to increase buy price (e.g., 10 for 10%)"))
    fld_buy_sum = fields.Float(string=_("Buy Sum"),help=_("Fixed amount to add to buy price"))
    fld_sell_update = fields.Selection([('ratio', _('Ratio')), ('sum', _('Sum'))], string=_("Sell Update Type"))
    fld_sell_ratio = fields.Float(
        string=_("Sell Ratio (%)"),
        help=_("Percentage to increase sell price (e.g., 10 for 10%)")
    )
    fld_sell_sum = fields.Float(
        string=_("Sell Sum"),
        help=_("Fixed amount to add to sell price")
    )
    fld_on_buy = fields.Boolean(
        string=_("Based on Buy Price"),
        default=True,
        help=_("Calculate sell ratio based on buy price instead of sell price")
    )


    def fnc_update_goods(self):
        """
        Update selected goods with new category, unit, alarms, and notes
        """
        catg = self.fld_category_id
        unit = self.fld_unit_id
        alarms = self.fld_alarms
        notes = self.fld_notes
        
        if not any([catg, unit, alarms, notes]):
            raise UserError(_('Please select at least one field to update'))
        
        active_ids = self.env['mdl_goods'].browse(self._context.get('active_ids'))
        if not active_ids:
            raise UserError(_('No goods selected for update'))
        
        updated_count = 0
        for rcrd in active_ids:
            write_dic = {}
            
            if catg:
                write_dic['fld_category_id'] = catg.id
            if notes:
                write_dic['fld_notes'] = notes
            if alarms and alarms > 0:
                write_dic['fld_alarms'] = alarms
            if unit:
                # Update Unit When The Same Of Catg_Unit Or Goods Is Not Used
                goods_ctg_unit_id = rcrd.fld_unit_id.fld_catg_id
                new_ctg_unit_id = unit.fld_catg_id
                is_used = rcrd.fnc_check_goods_usage()
                if (goods_ctg_unit_id == new_ctg_unit_id) or not is_used:
                    write_dic['fld_unit_id'] = unit.id
                else:
                    # Skip updating unit for this goods
                    continue
            
            if write_dic:
                rcrd.write(write_dic)
                updated_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Successfully updated %d goods') % updated_count,
                'type': 'success',
                'sticky': False,
            }
        }


    def fnc_update_prices(self):
        """
        Update prices for selected goods based on sum or ratio
        """
        buy_update = self.fld_buy_update
        buy_ratio = self.fld_buy_ratio
        buy_sum = self.fld_buy_sum
        sell_update = self.fld_sell_update
        sell_ratio = self.fld_sell_ratio
        sell_sum = self.fld_sell_sum
        on_buy = self.fld_on_buy
        
        # Validation
        validate = self._validate_prices_to_update()
        if not validate:
            raise UserError(_('Please select at least one price type to update'))
        
        if buy_update == 'ratio' and buy_ratio <= 0:
            raise UserError(_('Please provide buy ratio value'))
        if buy_update == 'sum' and buy_sum <= 0:
            raise UserError(_('Please provide buy sum value'))
        if sell_update == 'ratio' and sell_ratio <= 0:
            raise UserError(_('Please provide sell ratio value'))
        if sell_update == 'sum' and sell_sum <= 0:
            raise UserError(_('Please provide sell sum value'))
        
        active_ids = self.env['mdl_goods'].browse(self._context.get('active_ids'))
        if not active_ids:
            raise UserError(_('No goods selected for price update'))
        
        updated_count = 0
        for rcrd in active_ids:
            write_dic = {}
            buy = rcrd.fld_price_buy or 0
            sell = rcrd.fld_price_sell or 0
            ratio_on = buy if on_buy else sell
            
            # Calculate new prices
            if buy_update == 'sum':
                write_dic['fld_price_buy'] = buy + buy_sum
            elif buy_update == 'ratio':
                write_dic['fld_price_buy'] = buy + ((buy_ratio * buy) / 100)
            
            if sell_update == 'sum':
                write_dic['fld_price_sell'] = sell + sell_sum
            elif sell_update == 'ratio':
                write_dic['fld_price_sell'] = sell + ((sell_ratio * ratio_on) / 100)
            
            if write_dic:
                rcrd.write(write_dic)
                updated_count += 1
        
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': _('Success'),
        #         'message': _('Successfully updated prices for %d goods') % updated_count,
        #         'type': 'success',
        #         'sticky': False,
        #     }
        # }

    def _validate_prices_to_update(self):
        buy_update = self.fld_buy_update
        sell_update = self.fld_sell_update
        return buy_update or  sell_update


