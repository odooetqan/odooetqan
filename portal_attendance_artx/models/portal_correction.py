from odoo import models, fields

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

    def action_approve(self):
        """ Approve the correction and update hr.attendance record """
        for record in self:
            if record.state == 'pending':
                record.attendance_id.write({
                    'check_in': record.corrected_check_in,
                    'check_out': record.corrected_check_out,
                })
                record.state = 'approved'

    def action_reject(self):
        """ Reject the correction request """
        for record in self:
            if record.state == 'pending':
                record.state = 'rejected'
