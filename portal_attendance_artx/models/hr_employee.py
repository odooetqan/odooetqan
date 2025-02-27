from odoo import models, fields, api, _
from odoo.exceptions import UserError

# class HrContractHistory(models.Model):
#     _name = 'hr.contract.history'

#     time_credit = fields.Float(string="Time Credit")

class HrContractHistory(models.Model):
    _name = "hr.contract.history"
    _inherit = "hr.contract.history"
    
    time_credit = fields.Float(string="Time Credit")
    work_time_rate = fields.Float(string="Work Time Rate")

class AttendanceInherit(models.Model):
    _inherit = 'hr.attendance'

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
