from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time
import pytz


class HrAttendanceCorrection(models.Model):
    _name = 'hr.attendance.correction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Attendance Correction Request"

    employee_id = fields.Many2one('hr.employee', required=True)
    attendance_id = fields.Many2one('hr.attendance', required=True)

    original_check_in = fields.Datetime("Original Check In")
    original_check_out = fields.Datetime("Original Check Out")

    corrected_time = fields.Char("Corrected Time (HH:MM)", required=True)
    correction_type = fields.Selection([
        ('check_in', 'Check In'),
        ('check_out', 'Check Out')
    ], required=True)

    attachment = fields.Many2many('ir.attachment', string='Attachments')
    reason = fields.Text("Correction Reason", required=True)

    state = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')

    def action_approve(self):
        for rec in self:
            if rec.state != 'pending':
                continue

            attendance = rec.attendance_id
            if not attendance:
                raise ValidationError("No linked attendance record to correct.")

            try:
                hour, minute = map(int, rec.corrected_time.strip().split(':'))
            except Exception:
                raise ValidationError("Invalid time format. Please enter time as HH:MM.")

            user_tz = pytz.timezone(self.env.user.tz or 'UTC')

            if rec.correction_type == 'check_in':
                base_date = fields.Datetime.context_timestamp(rec, rec.original_check_in).date()
                local_dt = user_tz.localize(datetime.combine(base_date, time(hour, minute)))
                utc_dt = local_dt.astimezone(pytz.utc)
                attendance.write({'check_in': fields.Datetime.to_string(utc_dt)})
                rec.message_post(body=f"✅ Check-in updated to {utc_dt.strftime('%Y-%m-%d %H:%M')} UTC")

            elif rec.correction_type == 'check_out':
                base_date = fields.Datetime.context_timestamp(rec, rec.original_check_out).date()
                local_dt = user_tz.localize(datetime.combine(base_date, time(hour, minute)))
                utc_dt = local_dt.astimezone(pytz.utc)
                attendance.write({'check_out': fields.Datetime.to_string(utc_dt)})
                rec.message_post(body=f"✅ Check-out updated to {utc_dt.strftime('%Y-%m-%d %H:%M')} UTC")

            rec.state = 'approved'
            rec.message_post(body="🟢 Correction request approved.")

    def action_reject(self):
        for record in self:
            if record.state == 'pending':
                record.state = 'rejected'
                record.me
# class HrAttendanceCorrection(models.Model):
#     _name = 'hr.attendance.correction'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _description = "Attendance Correction Request"

#     employee_id = fields.Many2one('hr.employee', required=True)
#     attendance_id = fields.Many2one('hr.attendance', required=True)

#     original_check_in = fields.Datetime("Original Check In")
#     original_check_out = fields.Datetime("Original Check Out")

#     corrected_time = fields.Char("Corrected Time (HH:MM)", required=True)
#     correction_type = fields.Selection([
#         ('check_in', 'Check In'),
#         ('check_out', 'Check Out')
#     ], required=True)

#     attachment = fields.Many2many('ir.attachment', string='Attachments')
#     reason = fields.Text("Correction Reason", required=True)

#     state = fields.Selection([
#         ('pending', 'Pending Approval'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected')
#     ], default='pending')

#     def action_approve(self):
#         for rec in self:
#             if rec.state != 'pending':
#                 continue

#             attendance = rec.attendance_id
#             if not attendance:
#                 raise ValidationError("No linked attendance record to correct.")

#             try:
#                 hour, minute = map(int, rec.corrected_time.split(':'))
#             except Exception:
#                 raise ValidationError("Invalid time format. Please enter time as HH:MM.")

#             # Apply correction based on type
#             if rec.correction_type == 'check_in':
#                 base_date = rec.original_check_in.date()
#                 new_check_in = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
#                 attendance.write({'check_in': new_check_in})
#                 rec.message_post(body=f"✅ Approved correction. New <b>Check In</b>: {new_check_in.strftime('%Y-%m-%d %H:%M')}")

#             elif rec.correction_type == 'check_out':
#                 base_date = rec.original_check_out.date()
#                 new_check_out = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
#                 attendance.write({'check_out': new_check_out})
#                 rec.message_post(body=f"✅ Approved correction. New <b>Check Out</b>: {new_check_out.strftime('%Y-%m-%d %H:%M')}")

#             rec.state = 'approved'
#             rec.message_post(body="🟢 Correction request approved.")

    # def action_reject(self):
    #     for record in self:
    #         if record.state == 'pending':
    #             record.state = 'rejected'
    #             record.message_post(body="🔴 Correction request rejected.")

# # class HrAttendanceCorrection(models.Model):
# #     _name = 'hr.attendance.correction'
# #     _inherit = ['mail.thread', 'mail.activity.mixin']
# #     _description = "Attendance Correction Request"

# #     employee_id = fields.Many2one('hr.employee', required=True)
# #     attendance_id = fields.Many2one('hr.attendance', required=True)

# #     original_check_in = fields.Datetime("Original Check In")
# #     original_check_out = fields.Datetime("Original Check Out")

# #     corrected_time = fields.Char("Corrected Time (HH:MM)", required=True)
# #     correction_type = fields.Selection([
# #         ('check_in', 'Check In'),
# #         ('check_out', 'Check Out')
# #     ], required=True)

# #     attachment = fields.Many2many('ir.attachment', string='Attachments')
# #     reason = fields.Text("Correction Reason", required=True)

# #     state = fields.Selection([
# #         ('pending', 'Pending Approval'),
# #         ('approved', 'Approved'),
# #         ('rejected', 'Rejected')
# #     ], default='pending')

# #     def action_approve(self):
# #         for rec in self:
# #             if rec.state != 'pending':
# #                 continue

# #             if rec.correction_type == 'check_in':
# #                 base_date = rec.original_check_in.date()
# #                 hour, minute = map(int, rec.corrected_time.split(':'))
# #                 new_check_in = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
# #                 rec.attendance_id.check_in = new_check_in

# #             elif rec.correction_type == 'check_out':
# #                 base_date = rec.original_check_out.date()
# #                 hour, minute = map(int, rec.corrected_time.split(':'))
# #                 new_check_out = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
# #                 rec.attendance_id.check_out = new_check_out

# #             rec.state = 'approved'


# #     def action_reject(self):
# #         """ Reject the correction request """
# #         for record in self:
# #             if record.state == 'pending':
# #                 record.state = 'rejected'


# # from odoo import models, fields
# # from odoo.exceptions import ValidationError


# # class HrAttendanceCorrection(models.Model):
# #     _name = 'hr.attendance.correction'
# #     _inherit = ['mail.thread', 'mail.activity.mixin']  # ✅ Enables chatter

# #     _description = "Attendance Correction Request"

# #     employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
# #     attendance_id = fields.Many2one('hr.attendance', string="Attendance", required=True)

# #     original_check_in = fields.Datetime("Original Check In", required=True)
# #     original_check_out = fields.Datetime("Original Check Out", required=True)
# #     corrected_check_in = fields.Datetime("Corrected Check In", required=True)
# #     corrected_check_out = fields.Datetime("Corrected Check Out", required=True)
# #     attachment = fields.Many2many('ir.attachment', string='Attachments')

# #     reason = fields.Text("Correction Reason", required=True)
# #     state = fields.Selection([
# #         ('pending', 'Pending Approval'),
# #         ('approved', 'Approved'),
# #         ('rejected', 'Rejected')
# #     ], default='pending', string="Status", required=True)

# #     def action_submit(self):
# #         """Submit the correction request for approval."""
# #         self.write({'state': 'pending'})
# #         self.message_post(body="🟡 Attendance correction request submitted for approval.", subtype_xmlid="mail.mt_comment")


# #     # def action_approve(self):
# #     #     """Approve the correction and update hr.attendance record"""
# #     #     for record in self:
# #     #         if record.state == 'pending':
# #     #             attendance = record.attendance_id

# #     #             if not attendance:
# #     #                 raise ValidationError("No existing attendance record found.")

# #     #             # Check if there's already a check-in without a check-out
# #     #             if attendance.check_in and not attendance.check_out:
# #     #                 # Try to find a historical check_out for this check_in
# #     #                 last_attendance = self.env['hr.attendance'].search([
# #     #                     ('employee_id', '=', attendance.employee_id.id),
# #     #                     ('check_in', '<', attendance.check_in),
# #     #                     ('check_out', '!=', False)
# #     #                 ], order='check_out desc', limit=1)

# #     #                 if last_attendance:
# #     #                     raise ValidationError(f"Cannot correct attendance. The employee already has a previous check_out at {last_attendance.check_out}.")

# #     #                 # If no previous check_out, create one automatically
# #     #                 attendance.write({
# #     #                     'check_out': record.corrected_check_out or fields.Datetime.now(),
# #     #                 })

# #     #             # Now apply the correction
# #     #             attendance.write({
# #     #                 # 'check_in': record.corrected_check_in,
# #     #                 'check_out': record.corrected_check_out or attendance.check_out,  # Keep the auto-created check_out
# #     #             })

# #     #             record.state = 'approved'

# #     def action_approve(self):
# #         """ Approve the correction and update hr.attendance record """
# #         for record in self:
# #             if record.state == 'pending':
# #                 record.attendance_id.write({
# #                     # 'check_in': record.corrected_check_in,
# #                     'check_out': record.corrected_check_out,
# #                 })
# #                 record.state = 'approved'

# #     def action_reject(self):
# #         """ Reject the correction request """
# #         for record in self:
# #             if record.state == 'pending':
# #                 record.state = 'rejected'
