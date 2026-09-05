from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class Cls_isalls(models.Model):
    _name = 'mdl_isalls'
    _description = "Table Of Isalls"
    _order = " fld_sell_id,fld_num"


    fld_reg_date = fields.Date(string="Reg Date")
    fld_month = fields.Integer(string="Reg Month")
    fld_year = fields.Integer(string="Reg Year")
    fld_amount = fields.Float(string="Amount")
    fld_num = fields.Integer(string="Number")
    fld_collctr_isal_id = fields.Many2one('mdl_mandoops', string="Collector Isal", ondelete='restrict')
    fld_is_paid = fields.Boolean(string="Is Paid?",readonly=True)
    fld_is_printed = fields.Boolean(string="Is Printed?",readonly=True)

    fld_sell_id = fields.Many2one('mdl_sells', string="Sells ID", ondelete='cascade')
    active = fields.Boolean(default=True)

    fld_num_isalls = fields.Integer(related="fld_sell_id.fld_num_isalls", store=True)
    fld_mandoops = fields.Many2many(relation='mdl_isalls_mandoops_rel',column1='isall_id', column2='mandoop_id',related="fld_sell_id.fld_mandoops", store=True)
    fld_customer_id = fields.Many2one(related="fld_sell_id.fld_customer_id", store=True)
    fld_phone = fields.Char(related="fld_sell_id.fld_phone", store=True)
    fld_region_id = fields.Many2one(related="fld_sell_id.fld_region_id", store=True)
    fld_place_id = fields.Many2one(related="fld_sell_id.fld_place_id", store=True)
    fld_address = fields.Char(related="fld_sell_id.fld_address", store=True)



    def fnc_print_isalls_tahseel(self):
        """Print Isalls Tahseel report and mark as printed"""
        self.write({'fld_is_printed': True})
        return self.env.ref('super_market_installments.isalls_tahseel_action_report_id').sudo().report_action(self, data={})


    def fnc_paid_isalls(self, oper='<', cancel=False):
        """Mark installments as paid or cancel payment"""
        isalls_paid_str = ''
        slf = self.sorted(key=('id'), reverse=cancel)
        for rcrd in slf:
            isall_num = rcrd.fld_num
            sell_id = rcrd.fld_sell_id
            count_isalls_paid = self.env['mdl_isalls'].search_count(
                [('fld_sell_id', '=', sell_id.id), ('fld_num', oper, isall_num), ('fld_is_paid', '=', cancel)])
            if count_isalls_paid > 0:
                if isalls_paid_str != '':
                    isalls_paid_str += ' And '
                isalls_paid_str += str(isall_num) + ',' + sell_id.name
            else:
                rcrd.write({'fld_is_paid': not cancel})
        if isalls_paid_str != '':
            self.fnc_rais_error_paid(isalls_paid_str, not cancel)

    def fnc_rais_error_paid(self, str_error, paid=False):
        if paid:
            msg = _(
                'Can Not Pay Isalls Number (%s) \n There Is Lower Isall From The Same Sell_Qest Is Not Paid\n Paid It Before This!' % (
                    str_error))
        else:
            msg = _(
                'Can Not Cancel Paying Of Isall(s) Number (%s) \n There Is Above Isall From The Same Sell_Qest Is Paid\n Cancel Paying Of It Before This!' % (
                    str_error))
        raise UserError(msg)

    def fnc_cancel_received_isalls(self):
        """Cancel received installments by removing collector"""
        self.write({'fld_collctr_isal_id': False})

    def fnc_relay_isalls(self):
        """Relay installments to next month"""
        sells_id_lst = []
        for rcrd in self:
            isall_num = rcrd.fld_num
            is_paid = rcrd.fld_is_paid
            sell_id = rcrd.fld_sell_id
            if rcrd.fld_sell_id in sells_id_lst:
                raise UserError(_('The Isall Number (%s , %s) \n There Is Another Isall From The Same Sell_Qest \n Must Be One Isall From Sell_Qest!' % (isall_num, sell_id.name)))
            if is_paid:
                raise UserError(_('The Isall Number (%s , %s) Is Paid , You Can Not Relay It!' % (isall_num, sell_id.name)))
            sells_id_lst.append(rcrd.fld_sell_id)
            res = rcrd.env['mdl_isalls'].search([('fld_sell_id', '=', sell_id.id), ('fld_is_paid', '=', False),
                                                 ('fld_num', '>=', isall_num)])
            for rec in res:
                date_old = rec.fld_reg_date
                date_new = date_old + relativedelta(months=+1)
                rec.write({
                    'fld_reg_date': date_new,
                    'fld_month': date_new.month,
                    'fld_year': date_new.year
                })