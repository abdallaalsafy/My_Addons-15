from odoo import models, fields, api, _
from odoo.exceptions import UserError

class cls_update_goods(models.TransientModel):
    _inherit = 'wzrd_update_goods'

    fld_qst_update = fields.Selection([('ratio', 'Ratio'), ('sum', 'Sum')], string="Update Type")
    fld_qst_ratio = fields.Float(string="Ratio")
    fld_qst_sum = fields.Float(string="Sum")
    fld_qst_on_buy = fields.Boolean(string="On Price Buy", default=True)

    fld_hafez_update = fields.Selection([('ratio', 'Ratio'), ('sum', 'Sum')], string="Update Type")
    fld_hafez_ratio = fields.Float(string="Ratio")
    fld_hafez_sum = fields.Float(string="Sum")
    fld_hafez_on_buy = fields.Boolean(string="On Price Buy", default=True)

    def fnc_update_prices(self):
        """Update QST and Hafez prices for goods"""
        super().fnc_update_prices()

        hafez_update = self.fld_hafez_update
        hafez_ratio = self.fld_hafez_ratio
        hafez_sum = self.fld_hafez_sum

        qst_update = self.fld_qst_update
        qst_ratio = self.fld_qst_ratio
        qst_sum = self.fld_qst_sum

        qst_on_buy = self.fld_qst_on_buy
        hafez_on_buy = self.fld_hafez_on_buy

        if hafez_update == 'ratio' and hafez_ratio <= 0:
            raise UserError(_('Please provide hafez ratio value'))
        if hafez_update == 'sum' and hafez_sum <= 0:
            raise UserError(_('Please provide hafez sum value'))
        if qst_update == 'ratio' and qst_ratio <= 0:
            raise UserError(_('Please provide qst ratio value'))
        if qst_update == 'sum' and qst_sum <= 0:
            raise UserError(_('Please provide qst sum value'))

        write_dic = {}
        active_ids = self.env['mdl_goods'].browse(self._context.get('active_ids'))
        
        for rcrd in active_ids:
            buy = rcrd.fld_price_buy or 0
            qst = rcrd.fld_price_qst or 0
            hafez = rcrd.fld_hafez or 0

            qst_ratio_on = buy if qst_on_buy else qst
            hafez_ratio_on = buy if hafez_on_buy else hafez
            
            # Update qst fields
            if qst_update == 'sum':
                write_dic['fld_price_qst'] = qst + qst_sum
            elif qst_update == 'ratio':
                write_dic['fld_price_qst'] = qst + ((qst_ratio * qst_ratio_on) / 100)
                
            # Update hafez fields
            if hafez_update == 'sum':
                write_dic['fld_hafez'] = hafez + hafez_sum
            elif hafez_update == 'ratio':
                write_dic['fld_hafez'] = hafez + ((hafez_ratio * hafez_ratio_on) / 100)

            # Apply the update
            if write_dic:
                rcrd.write(write_dic)

    def _validate_prices_to_update(self):
        validate = super()._validate_prices_to_update()

        qst_update = self.fld_qst_update
        hafez_update = self.fld_hafez_update
        return qst_update or hafez_update or validate
