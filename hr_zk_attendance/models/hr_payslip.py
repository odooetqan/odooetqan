
import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta  # ✅ Ensure timedelta is imported
from pytz import timezone, utc  # ✅ Import timezone functions

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    total_late_minutes = fields.Float(string="Total Lateness (Minutes)", compute="_compute_attendance_data", store=True)
    total_overtime_minutes = fields.Float(string="Total Overtime (Minutes)", compute="_compute_attendance_data", store=True)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_attendance_data(self):
        """Calculate total lateness and overtime for the payslip period."""
        for payslip in self:
            if not payslip.employee_id:
                payslip.total_late_minutes = 0
                payslip.total_overtime_minutes = 0
                continue

            attendance_records = self.env['hr.attendance'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('check_in', '>=', payslip.date_from),
                ('check_out', '<=', payslip.date_to)
            ])

            payslip.total_late_minutes = sum(att.late_minutes for att in attendance_records)
            payslip.total_overtime_minutes = sum(att.overtime_minutes for att in attendance_records)
