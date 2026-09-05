from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.public_class import MainClass


class cls_buys(models.Model):
    _name = 'mdl_buys'
    _description = 'Table Of All Fatoras Buys'
    _rec_name = "fld_sequence"
    _sql_constraints = [('unique_buys_sequences', 'unique (fld_sequence)', 'The sequence Is Existe Before')]

    def fnc_renum(self): MainClass().fnc_renum(self)

    @api.model
    def fnc_maxum(self): return MainClass().fnc_maxum(self, 'fld_sequence')

    @api.onchange("fld_sequence_chk")
    def fnc_change_sequence(self):
        if not self.fld_sequence_chk:
            x_buy_rcrd = self.search([('id', '=', self._origin.id)])
            if x_buy_rcrd:
                self.fld_sequence = x_buy_rcrd.fld_sequence
            else:
                self.fld_sequence = self.fnc_maxum()

    @api.depends('fld_buygoods_ids')
    def fnc_totall(self):
        vrb = 0
        for obj in self.fld_buygoods_ids:
            vrb = vrb + obj.fld_calc_price
        self.fld_totall= vrb

    @api.onchange('fld_buygoods_ids')
    def fnc_check_repeat(self):
        for obj in self.fld_buygoods_ids:
            for obj2 in self.fld_buygoods_ids:
                if obj2.fld_goods_id == obj.fld_goods_id and obj2.id != obj.id:
                    raise UserError(_('The Goods Is Existing Before To This Fatora'))

    @api.depends('fld_paying', 'fld_totall')
    def fnc_remain(self): self.fld_remain = self.fld_totall - self.fld_paying

    @api.constrains('fld_paying', 'fld_buygoods_ids')
    def fnc_chek_fields(self):
        if len(self.fld_buygoods_ids) == 0:
            raise ValidationError(_('Fatora Must Be Have At Least One Goods'))
        if self.fld_paying > self.fld_totall:
            raise ValidationError(_('Paying Of Fatora Must Not Be Greater Than Totall Fatora'))

    def fnc_stores_goods(self, x_store_id, x_buy_goods_ids, x_unlink=False):
        x_tbl_buys_goods = self.env['mdl_buys_goods']
        x_tbl_stores_goods = self.env['mdl_stores_goods']
        x_tbl_goods = self.env['mdl_goods']
        x_tbl_buy_goods_in = self.env['mdl_buys_goods_in']
        x_old_store_id = self.fld_store_id.id
        x_oper = 2 if x_unlink else 4
        if not x_buy_goods_ids:
            x_buy_goods_ids=[]
            for rcrd in self.fld_buygoods_ids:
                x_buy_goods_ids.append([x_oper, rcrd.id, False])
        for lst in x_buy_goods_ids:
            if lst[0] == 1 and not x_store_id and not lst[2].get('fld_goods_id') and not lst[2].get('fld_goods_num'):continue
            if lst[0] != 0:
                x_buy_goods_rcrd = x_tbl_buys_goods.search([('id', '=', lst[1])])
                x_old_goods_id = x_buy_goods_rcrd.fld_goods_id.id
                x_old_goods_num = x_buy_goods_rcrd.fld_goods_num
                x_old_stores_goods_rcrd = x_tbl_stores_goods.search([('fld_goods_id', '=', x_old_goods_id), ('fld_store_id', '=', x_old_store_id)])
                x_old_stores_goods_id = x_old_stores_goods_rcrd.id
                x_old_store_goods_num = x_old_stores_goods_rcrd.fld_goods_num
                x_tbl_stores_goods.browse(x_old_stores_goods_id).update({'fld_goods_num': x_old_store_goods_num - x_old_goods_num})
            if lst[0] != 2:
                if lst[0] != 4 and lst[2].get('fld_goods_id'):
                    x_goods_id = lst[2].get('fld_goods_id')
                else:
                    x_goods_id = x_old_goods_id

                if lst[0] != 4 and lst[2].get('fld_goods_num'):
                    x_goods_num = lst[2].get('fld_goods_num')
                else:
                    x_goods_num = x_old_goods_num
                    x_goods_rcrd = x_tbl_goods.search([('id', '=', x_goods_id)])
                    x_class_id = x_goods_rcrd.fld_class_id.id
                if not x_store_id: x_store_id = x_old_store_id

                x_stores_goods_rcrd = x_tbl_stores_goods.search([('fld_goods_id', '=', x_goods_id), ('fld_store_id', '=', x_store_id)])
                if x_stores_goods_rcrd:
                    x_stores_goods_id = x_stores_goods_rcrd.id
                    x_store_goods_num = x_stores_goods_rcrd.fld_goods_num
                    x_tbl_stores_goods.browse(x_stores_goods_id).update({'fld_goods_num': x_store_goods_num + x_goods_num})
                else:
                    x_tbl_stores_goods.create({'fld_store_id': x_store_id, 'fld_class_id': x_class_id, 'fld_goods_id': x_goods_id, 'fld_goods_num': x_goods_num})
            x_tbl_buy_goods_in.create(
                {'fld_store_id': x_store_id, 'fld_class_id': x_class_id, 'fld_goods_id': x_goods_id,
                 'fld_goods_num': x_goods_num})

    def fnc_chk_stores_goods(self, x_store_id, x_buy_goods_ids, x_unlink=False):
        # ------------- Make List Of New Goods From  New Data ---------------------------
        if not x_unlink:
            x_new_buy_goods_ids = []
            x_tbl_buys_goods = self.env['mdl_buys_goods']
            if x_buy_goods_ids:
                for lst in x_buy_goods_ids:
                    if lst[0] == 2: continue
                    if lst[0] == 0: x_new_buy_goods_ids.append(lst[2])
                    if lst[0] == 1 or lst[0] == 4:
                        x_buy_goods_rcrd = x_tbl_buys_goods.search([('id', '=', lst[1])])
                        if lst[0] == 4 or not lst[2].get('fld_goods_id'):
                            x_goods_id = x_buy_goods_rcrd.fld_goods_id.id
                        else:
                            x_goods_id = lst[2].get('fld_goods_id')
                        if lst[0] == 4 or not lst[2].get('fld_goods_num'):
                            x_goods_num = x_buy_goods_rcrd.fld_goods_num
                        else:
                            x_goods_num = lst[2].get('fld_goods_num')
                        x_new_buy_goods_ids.append({'fld_goods_id': x_goods_id, 'fld_goods_num': x_goods_num})
            else:
                for rcrd in self.fld_buygoods_ids:
                    x_goods_id = rcrd.fld_goods_id.id
                    x_goods_num = rcrd.fld_goods_num
                    x_new_buy_goods_ids.append({'fld_goods_id': x_goods_id, 'fld_goods_num': x_goods_num})
            # ----------------------------------------
        x_tbl_stores_goods = self.env['mdl_stores_goods']
        x_old_store_id = self.fld_store_id.id
        for rcrd in self.fld_buygoods_ids:
            x_old_goods_id = rcrd.fld_goods_id.id
            x_old_goods_num = rcrd.fld_goods_num
            x_mins_goods_num = x_old_goods_num
            x_stores_goods_rcrd = x_tbl_stores_goods.search([('fld_goods_id', '=', x_old_goods_id), ('fld_store_id', '=', x_old_store_id)])
            x_goods_num_in_store = x_stores_goods_rcrd.fld_goods_num
            if not x_unlink:
                for lst in x_new_buy_goods_ids:
                    x_goods_id = lst['fld_goods_id']
                    x_goods_num = lst['fld_goods_num']
                    if x_old_goods_id == x_goods_id:
                        x_mins_goods_num = x_old_goods_num - x_goods_num if x_old_store_id == x_store_id else x_old_goods_num
                        break
                    elif x_new_buy_goods_ids.index(lst) == len(x_new_buy_goods_ids)-1:
                        x_mins_goods_num = x_old_goods_num
            if x_goods_num_in_store < x_mins_goods_num:
                raise ValidationError(_("""The Num Of Goods In Store Is Lower Than You Want To Delete 
                \n The Goods: %s \n Num To Delete Is: %d \n Num In Store: %d""" %(rcrd.fld_goods_id.name, x_mins_goods_num, x_goods_num_in_store)))

    @api.model
    def create(self, vals):
        x_buy_goods_ids = vals.get('fld_buygoods_ids')
        x_store_id = vals.get('fld_store_id')
        self.fnc_stores_goods(x_store_id, x_buy_goods_ids)
        return super(cls_buys, self).create(vals)

    def write(self, vals):
        x_buy_goods_ids = vals.get('fld_buygoods_ids')
        x_store_id = vals.get('fld_store_id')
        if x_buy_goods_ids or x_store_id:
            self.fnc_chk_stores_goods(x_store_id, x_buy_goods_ids)
            self.fnc_stores_goods(x_store_id, x_buy_goods_ids)
        return super(cls_buys, self).write(vals)

    def unlink(self):
        x_store_id = self.fld_store_id.id
        self.fnc_chk_stores_goods(x_store_id, [], True)
        self.fnc_stores_goods(x_store_id, [], True)
        return super(cls_buys, self).unlink()

    fld_sequence = fields.Integer(string='The Sequence', required=True, index=True, default=fnc_maxum)
    fld_sequence_chk = fields.Boolean(string="Choose", help='To Change Sequence')
    fld_paying = fields.Float(string='The Paying', digits=(8, 2))
    fld_date = fields.Date(string='The Date', default=fields.Date.today, required=True)
    fld_notes = fields.Text(string='Notes')
    fld_totall = fields.Float(string='The Totall', digits=(8, 2), store=True, compute='fnc_totall')
    fld_remain = fields.Float(string='The Remain', digits=(8, 2), store=True, compute='fnc_remain')
    fld_is_old = fields.Boolean()

    fld_store_id = fields.Many2one('mdl_stores', string="Store Name", required=True, ondelete="restrict")
    fld_customer_id = fields.Many2one('mdl_customers', string="customer Name", required=True, ondelete="restrict")
    fld_buygoods_ids = fields.One2many('mdl_buys_goods', 'fld_buy_id', string="The Goods")
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')
