from odoo import models, fields, api, _
from odoo.exceptions import UserError



#################################################################correction mdel 
class HRAttendanceCorrection(models.Model):
    _name = 'hr.attendance.correction'
    _description = 'Attendance Correction Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # ✅ Enables chatter

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    check_in = fields.Datetime(string='Requested Check-In', required=True, tracking=True)
    check_out = fields.Datetime(string='Requested Check-Out', required=True, tracking=True)
    note = fields.Text(string='Reason for Correction', tracking=True)
    attachment = fields.Many2many('ir.attachment', string='Attachments')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)  # ✅ Tracking Enabled

    approver_id = fields.Many2one('res.users', string='Approver')

    def action_submit(self):
        """Submit the correction request for approval."""
        self.write({'state': 'submitted'})
        self.message_post(body="🟡 Attendance correction request submitted for approval.", subtype_xmlid="mail.mt_comment")

    def action_approve(self):
        """Approve the correction request and update hr.attendance."""
        hr_attendance = self.env['hr.attendance'].create({
            'employee_id': self.employee_id.id,
            'check_in': self.check_in,
            'check_out': self.check_out,
        })
        self.write({'state': 'approved'})
        self.message_post(body=f"✅ Request approved. Attendance record created: {hr_attendance.id}", subtype_xmlid="mail.mt_comment")

    def action_reject(self):
        """Reject the correction request."""
        self.write({'state': 'rejected'})
        self.message_post(body="❌ Attendance correction request rejected.", subtype_xmlid="mail.mt_comment")

# class HRAttendanceCorrection(models.Model):
#     _name = 'hr.attendance.correction'
#     _description = 'Attendance Correction Request'
#     _inherit = ['mail.thread', 'mail.activity.mixin']  # Enables chatter and activities

#     employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self._default_employee, tracking=True)
#     check_in = fields.Datetime(string='Requested Check-In', required=True, tracking=True)
#     check_out = fields.Datetime(string='Requested Check-Out', required=True, tracking=True)
#     note = fields.Text(string='Reason for Correction', tracking=True)
#     attachment = fields.Many2many('ir.attachment', string='Attachments')
    
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('submitted', 'Submitted'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#     ], string='Status', default='draft', tracking=True)

#     approver_id = fields.Many2one('res.users', string='Approver')
    
#     def _default_employee(self):
#         return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

#     def action_submit(self):
#         """Submit the correction request for approval."""
#         self.write({'state': 'submitted'})
#         self.message_post(body="Attendance correction request submitted for approval.")

#     def action_approve(self):
#         """Approve the correction request and update hr.attendance."""
#         hr_attendance = self.env['hr.attendance'].create({
#             'employee_id': self.employee_id.id,
#             'check_in': self.check_in,
#             'check_out': self.check_out,
#         })
#         self.write({'state': 'approved'})
#         self.message_post(body=f"Request approved. Attendance record created: {hr_attendance.id}")

#     def action_reject(self):
#         """Reject the correction request."""
#         self.write({'state': 'rejected'})
#         self.message_post(body="Attendance correction request rejected.")


#################################################################End correction model 



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
