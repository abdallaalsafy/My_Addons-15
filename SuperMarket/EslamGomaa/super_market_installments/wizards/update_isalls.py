from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class Cls_update_isalls(models.TransientModel):
    _name = 'wzrd_update_isalls'
    _description = 'Wizard Of Updating Isalls'


    def fnc_get_default_sell_id(self):
        """Get default sell ID from context"""
        active_id = self.env['mdl_sells'].browse(self._context.get('active_id'))
        return active_id.id

    fld_sell_id = fields.Many2one('mdl_sells', string="Sells ID", default=fnc_get_default_sell_id, required=True)
    fld_isalls_ids = fields.One2many('mdl_isalls', related="fld_sell_id.fld_isalls_ids", string="Installments", readonly=True,)

    fld_reg_date = fields.Date(string="Reg Date", help="New registration date for installments")
    fld_amount = fields.Float(string="New Amount", help="New amount for installments")

    fld_from = fields.Integer(string="From Isall Number", required=True)
    fld_to = fields.Integer(string="To Isall Number", required=True)


    def action_update_installments(self):
        """Validate and preview changes before applying"""

        # Basic validation
        if not self.fld_sell_id:
            return self.fnc_message_warring(_("No sell record selected"))
        
        isalls_ids = self.fld_isalls_ids.sorted(key='fld_num')
        if not isalls_ids:
            raise UserError(_("No installments found"))

        # Date validation
        reg_date = self.fld_reg_date
        date_sell = self.fld_sell_id.fld_date
        if reg_date and (reg_date < date_sell):
            raise UserError(_("The Reg_Date Is Lower Than The Date Of sell"))

        # Range validation
        num_from = self.fld_from
        num_to = self.fld_to
        num_isalls = len(isalls_ids)
        
        if num_from <= 0 or num_from > num_isalls or num_to <= 0 or num_to > num_isalls:
            raise UserError(_("Num_From Or Num_To Is Out Of Range"))

        # Determine direction and calculate step
        direction_up = num_from > num_to
        step = -1 if direction_up else 1
        num_to_edit = abs(num_to - num_from) + 1

        # Validate num_to_edit
        if num_to_edit <= 1:
            raise UserError(_("Num_To Edit must be above 1"))

        change_mount = False
        change_reg_date = False
        # Date validation logic
        if reg_date:
            change_reg_date = self._validate_date_changes(isalls_ids, num_from, num_to, reg_date, date_sell, direction_up, num_to_edit)

        # Amount validation logic
        amount = self.fld_amount
        if amount > 0:
            change_mount = self._validate_amount_changes(isalls_ids, num_from, num_to, amount, num_to_edit,step)

        if change_reg_date or change_mount:
            self.fnc_update_Isalls(isalls_ids, num_from, num_to, reg_date, num_to_edit,amount,step)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


    def _validate_date_changes(self, isalls_ids, num_from, num_to, reg_date, date_sell, direction_up, num_to_edit):
        """Validate date changes for installments"""
        num_isalls = len(isalls_ids)

        if direction_up:  # Going backwards (higher numbers to lower)
            # Check against next installment
            if num_from != num_isalls and reg_date > isalls_ids[num_from].fld_reg_date:
                raise UserError(_("Reg Date Of Isall Is Greater Than The Next Isall"))
            
            # Check if earliest date is valid
            if num_to == 1:
                earliest_date = reg_date + relativedelta(months=-(num_to_edit-1))
                if earliest_date < date_sell:
                    raise UserError(_("Reg Date Of Isall Is Not Suitable"))
            else:
                earliest_date = reg_date + relativedelta(months=-(num_to_edit-1))
                if earliest_date < isalls_ids[num_to-2].fld_reg_date:
                    raise UserError(_("Reg Date Of Isall Is Not Suitable"))
        else:  # Going forwards (lower numbers to higher)
            # Check against previous installment
            if num_from != 1 and reg_date < isalls_ids[num_from-2].fld_reg_date:
                raise UserError(_("Reg Date Of Isall Is Lower Than The Previous Isall"))
            
            # Check if latest date is valid
            if num_to != num_isalls:
                latest_date = reg_date + relativedelta(months=(num_to_edit-1))
                if latest_date > isalls_ids[num_to].fld_reg_date:
                    raise UserError(_("Reg Date Of Isall Is Not Suitable"))

        return True

    def _validate_amount_changes(self, isalls_ids, num_from, num_to, amount, num_to_edit,step):
        """Validate amount changes for installments"""

        # Calculate total amount for selected installments
        total_current_amount = sum(isalls_ids[i-1].fld_amount for i in range(num_from, num_to + step,step))
        
        # Check if new amount is reasonable
        if (total_current_amount-amount) < (num_to_edit-1):
            raise UserError(_("Amount Of Isall Is Too High"))

        return True

    def fnc_update_Isalls(self, isalls_ids, num_from, num_to, reg_date, num_to_edit,amount,step):
        """Apply the updates to installments"""

        # Calculate total amount for selected installments
        amount_isalls_edit = sum(isalls_ids[i - 1].fld_amount for i in range(num_from, num_to + step,step))

        counter = 0
        current_date = reg_date
        for i in range(num_from, num_to + step,step):
            installment = isalls_ids[i-1]
            update_data = {}
            
            # Update amount if changed
            if amount > 0:
                update_data['fld_amount'] = amount
                amount_isalls_edit -= amount
                counter += 1
                if i != num_to:
                    amount = amount_isalls_edit//(num_to_edit-counter)

            # Update date if changed
            if reg_date:
                update_data.update({
                    'fld_reg_date': current_date,
                    'fld_month': current_date.month,
                    'fld_year': current_date.year,
                })
                if i != num_to:
                    current_date += relativedelta(months=step)
            
            # Apply the update
            if update_data:
                installment.write(update_data)