from odoo import models, fields, api, _
from odoo.exceptions import UserError

# class HrContractHistory(models.Model):
#     _name = 'hr.contract.history'

#     # time_credit = fields.Float(string="Time Credit")
# # class HrContractHistory(models.Model):
# #     _name = 'hr.contract.history'
# #     _description = "Contract History"

#     reference_yearly_cost = fields.Monetary(
#         string="Yearly Cost",
#         currency_field='currency_id'
#     )
#     currency_id = fields.Many2one('res.currency', string="Currency")

# class HrContractHistory(models.Model):
#     _name = 'hr.contract.history'
#     # _description = "Contract History"
    # _auto = True  # ✅ هذا مهم! يجعل Odoo ينشئ جدول حقيقي

    # # حقولك...
    # currency_id = fields.Many2one('res.currency', string="Currency")
    # reference_yearly_cost = fields.Monetary(
    #     string="Yearly Cost",
    #     currency_field='currency_id'
    # )


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    overtime_minutes = fields.Integer(string="Overtime (Minutes)", compute="_compute_overtime")

    def _compute_overtime(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                total_worked = (rec.check_out - rec.check_in).total_seconds() / 60
                rec.overtime_minutes = max(0, total_worked - 480)  # Assuming 8 hours (480 min) is normal work time
            else:
                rec.overtime_minutes = 0

class HrContractHistory(models.Model):
    _name = "hr.contract.history"
    _inherit = "hr.contract.history"
    
    time_credit = fields.Float(string="Time Credit")
    work_time_rate = fields.Float(string="Work Time Rate")

# class AttendanceInherit(models.Model):
#     _inherit = 'hr.attendance'

class LeaveInherit(models.Model):
    _inherit = 'hr.leave'

class LeaveTypeInherit(models.Model):
    _inherit = 'hr.leave.type'

class EmployeePublicInherit(models.Model):
    _inherit = 'hr.employee.public'

class ResPartner(models.Model):
    _inherit = 'res.partner'


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    portal_user_created = fields.Boolean(string="Portal User Created", default=False)

    def action_create_portal_user(self):
        self.ensure_one()

        # Create user as a Portal User
        user_vals = {
            'name': self.name,
            'login': self.work_email or self.private_email,
            'email': self.work_email or self.private_email,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])]  # Assign portal group
        }
        user = self.env['res.users'].create(user_vals)

        # Link the created user to the employee
        self.user_id = user.id
        self.portal_user_created = True

        return {
            'name': _('Portal User Created'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.users',
            'res_id': user.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
