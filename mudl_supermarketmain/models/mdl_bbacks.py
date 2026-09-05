from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from mudl_supermarketmain.public_class import MainClass


class ClsBbacks(models.Model):
    _name = 'tbl_bbacks'
    _description = 'Table Of All Fatoras Buys Back'
    _rec_name = 'fld_num_bback'

    def fnc_renum(self): MainClass().fnc_renum(self)  # دالة توليد أرقام متسلسلة للفواتير خلال عرضها في الوضع الشجري
# OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    @api.model  # دالة عمل قيمة إفتراضية لرقم الفاتورة خلال عمل فاتورة جديدة
    def fnc_maxum(self): return MainClass().fnc_maxum(self, 'fld_num_bback')
# OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    @api.depends('fld_bback_goods_ids')
    def fnc_totall_bback(self): self.fld_totall_bback = self.fnc_totall_goods()

    @api.depends('fld_bback_paying', 'fld_bback_goods_ids')  # دالة تعدل خانة باقي الفاتورة عند تغير قيمة المدفوعات أو خانة إجمالي الفاتورة
    def fnc_remain_bback(self): self.fld_remain_bback = self.fnc_totall_goods() - self.fld_bback_paying

    def fnc_totall_goods(self):
        vrb = 0
        for obj in self.fld_bback_goods_ids:
            vrb = vrb + obj.fld_price_in_num
        return vrb
# OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO

    @api.onchange('fld_bback_goods_ids')
    def fnc_no_same_goods(self):  # دالة تمنع من تكرار منتج داخل منتجات الفاتورة
        for obj in self.fld_bback_goods_ids:
            vrb = obj.fld_goods_id
            vrb2 = 0
            for obj2 in self.fld_bback_goods_ids:
                if vrb == obj2.fld_goods_id:
                    vrb2 = vrb2 + 1
            if vrb2 > 1:
                raise ValidationError(_('Fatora Must Be Not Have The Same Goods'))
# # OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO

    # ====== دالة التحقق قبل حفظ الفاتورة=======
    # التحقق من ان رقم الفاتورة غير موجود
    # التحقق من أن رقم الفاتورة لايساوي صفر
    # التحقق من وجود منتجات بالفاتورة
    @api.constrains('fld_num_bback', 'fld_bback_paying', 'fld_bback_date')
    def fnc_unique_field(self):
        obj2 = self.search([('fld_num_bback', '=', self.fld_num_bback), ('id', '!=', self.id)])
        if obj2:
            raise ValidationError(_('The Number Of Fatora Buy Is Existing'))
        if self.fld_num_bback <= 0:
            self.fld_num_bback = self.fnc_maxum()
        if len(self.fld_buy_goods_ids) == 0:
            raise ValidationError(_('Fatora Must Be Have At Least One Goods'))
        if self.fld_bback_paying > self.fld_totall_bback:
            raise ValidationError(_('Paying Of Fatora Must Not Be Greater Than Totall Fatora'))
        if self.fld_bback_date > self.create_date.date():  # هذه الحالة تنفعنا في التعديل لأني لم أعرف تحجيم التاريخ لتاريخ الأنشاء خلال التعديل
            raise ValidationError(_('The Date Is Greater Than The Date Of Creating'))
# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    fld_num_bback = fields.Integer(string='Fatora Buy Back Number', required=True, index=True, default=fnc_maxum)
    fld_bback_paying = fields.Float(string='Paying Of Buy Back', digits=(8, 2))
    fld_bback_date = fields.Date(string='Date Of Buy Back', default=fields.Date.today, required=True)
    fld_bback_notes = fields.Text(string='Notes')
    fld_totall_bback = fields.Float(string='Totall Of Fatora Buy Back', digits=(8, 2), store=True, compute='fnc_totall_bback')
    fld_remain_bback = fields.Float(string='Remain Of Fatora Buy Back', digits=(8, 2), store=True, compute='fnc_remain_bback')

    fld_store_id = fields.Many2one('tbl_stores', string="Store Name", required=True, ondelete="restrict", domain="[('fld_store_del', '=', False)]")
    fld_customer_id = fields.Many2one('tbl_customers', string="customer Name", required=True, ondelete="restrict", domain="[('fld_customer_del', '=', False)]")
    fld_bback_goods_ids = fields.One2many('tbl_bbackgoods', 'fld_bback_id', string="Goods Of Fatora Buy Back")
    fld_sonum = fields.Integer(string='SoNum', compute='fnc_renum')
