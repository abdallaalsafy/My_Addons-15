from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .utils import (is_invalid_national_id)

class cls_customers(models.Model):
    _inherit = 'mdl_customers'
    _sql_constraints = [('uniqueCustomersCode', 'unique (fld_code)', 'The Code Nation Is Existe Before')]


    fld_code = fields.Char(string='Code Nation', size=14)
    fld_region_id = fields.Many2one("mdl_regions", string="Region", ondelete="restrict")
    fld_place_id = fields.Many2one("mdl_places", string="Place", domain="[('fld_region_id', '=?', fld_region_id)]", ondelete="restrict")

    # =================== Onchange Functions ==========================
    @api.onchange('fld_region_id')
    def _onchange_region(self):
        if (self.fld_region_id and self.fld_region_id != self.fld_place_id.fld_region_id) or not self.fld_region_id:
            self.fld_place_id = False

    @api.onchange('fld_place_id')
    def _onchange_place(self):
        if self.fld_place_id and self.fld_region_id != self.fld_place_id.fld_region_id:
            self.fld_region_id = self.fld_place_id.fld_region_id

    # ==================== Constraints =============================
    @api.constrains('fld_code')
    def _check_unique_id_number(self):
        """
        Check if ID number is unique when provided.
        """
        for record in self:
            if record.fld_code and is_invalid_national_id(record.fld_code):
                raise ValidationError(_(
                    "Invalid Egyptian National ID format! "
                    "Please enter a valid 14-digit national ID number."))

    # ==================== Compute Functions =========================
    @api.depends('fld_sells_ids', 'fld_sells_r_ids', 'fld_customers_in_ids', 'fld_customers_out_ids',
                 'fld_sells_ids.fld_total', 'fld_sells_ids.fld_discount', 'fld_sells_ids.fld_is_qst',
                 'fld_sells_r_ids.fld_total', 'fld_sells_r_ids.fld_discount', 'fld_sells_r_ids.fld_is_qst',
                 'fld_customers_in_ids.fld_paying', 'fld_customers_out_ids.fld_paying',
                 'fld_sells_ids.fld_total_qst', 'fld_sells_r_ids.fld_total_qst')
    def _compute_balance(self):
        for customer in self:
            # Calculate total sales amount
            total_sales = sum((sell.fld_total - sell.fld_discount) for sell in customer.fld_sells_ids if not sell.fld_is_qst)
            total_sales_qst = sum((sell.fld_total_qst - sell.fld_discount) for sell in customer.fld_sells_ids if sell.fld_is_qst)
            total_return_sales = sum((sell.fld_total - sell.fld_discount) for sell in customer.fld_sells_r_ids if not sell.fld_is_qst)
            total_return_sales_qst = sum((sell.fld_total_qst - sell.fld_discount) for sell in customer.fld_sells_r_ids if sell.fld_is_qst)

            # Calculate total payments
            total_payments_in = sum(payment.fld_paying for payment in customer.fld_customers_in_ids)
            total_payments_out = sum(payment.fld_paying for payment in customer.fld_customers_out_ids)

            # Calculate totals
            customer.total_sales = total_sales_qst + total_sales - total_return_sales - total_return_sales_qst
            customer.total_payments = total_payments_out - total_payments_in
            customer.balance = customer.total_sales + customer.total_payments