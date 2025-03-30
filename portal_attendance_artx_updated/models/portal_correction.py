from odoo import models, fields
from odoo.exceptions import ValidationError


class HrAttendanceCorrection(models.Model):
    _name = 'hr.attendance.correction'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # ✅ Enables chatter

    _description = "Attendance Correction Request"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    attendance_id = fields.Many2one('hr.attendance', string="Attendance", required=True)

    original_check_in = fields.Datetime("Original Check In", required=True)
    original_check_out = fields.Datetime("Original Check Out", required=True)
    corrected_check_in = fields.Datetime("Corrected Check In", required=True)
    corrected_check_out = fields.Datetime("Corrected Check Out", required=True)
    attachment = fields.Many2many('ir.attachment', string='Attachments')

    reason = fields.Text("Correction Reason", required=True)
    state = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending', string="Status", required=True)

    def action_submit(self):
        """Submit the correction request for approval."""
        self.write({'state': 'pending'})
        self.message_post(body="🟡 Attendance correction request submitted for approval.", subtype_xmlid="mail.mt_comment")


    # def action_approve(self):
    #     """Approve the correction and update hr.attendance record"""
    #     for record in self:
    #         if record.state == 'pending':
    #             attendance = record.attendance_id

    #             if not attendance:
    #                 raise ValidationError("No existing attendance record found.")

    #             # Check if there's already a check-in without a check-out
    #             if attendance.check_in and not attendance.check_out:
    #                 # Try to find a historical check_out for this check_in
    #                 last_attendance = self.env['hr.attendance'].search([
    #                     ('employee_id', '=', attendance.employee_id.id),
    #                     ('check_in', '<', attendance.check_in),
    #                     ('check_out', '!=', False)
    #                 ], order='check_out desc', limit=1)

    #                 if last_attendance:
    #                     raise ValidationError(f"Cannot correct attendance. The employee already has a previous check_out at {last_attendance.check_out}.")

    #                 # If no previous check_out, create one automatically
    #                 attendance.write({
    #                     'check_out': record.corrected_check_out or fields.Datetime.now(),
    #                 })

    #             # Now apply the correction
    #             attendance.write({
    #                 # 'check_in': record.corrected_check_in,
    #                 'check_out': record.corrected_check_out or attendance.check_out,  # Keep the auto-created check_out
    #             })

    #             record.state = 'approved'

    def action_approve(self):
        """ Approve the correction and update hr.attendance record """
        for record in self:
            if record.state == 'pending':
                record.attendance_id.write({
                    # 'check_in': record.corrected_check_in,
                    'check_out': record.corrected_check_out,
                })
                record.state = 'approved'

    def action_reject(self):
        """ Reject the correction request """
        for record in self:
            if record.state == 'pending':
                record.state = 'rejected'
