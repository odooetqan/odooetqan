from odoo import api, fields, models, tools
from datetime import datetime, timedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    deduction_multiplier = fields.Float(string='Deduction Multiplier', default=1.0)
    allowance_multiplier = fields.Float(string='Allowance Multiplier', default=1.0)
    per_minute_rate = fields.Float(string='Per Minute Rate', compute='_compute_per_minute_rate')

    def _compute_per_minute_rate(self):
        for employee in self:
            if employee.contract_id and employee.contract_id.resource_calendar_id:
                daily_minutes = employee.contract_id.resource_calendar_id.hours_per_day * 60
                employee.per_minute_rate = employee.contract_id.wage / daily_minutes if daily_minutes else 0.0

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    lateness = fields.Float(string='Lateness (minutes)', compute='_compute_lateness', store=True)
    shift_start = fields.Datetime(string='Shift Start')
    shift_end = fields.Datetime(string='Shift End')
    deduction_amount = fields.Float(string='Deduction Amount', compute='_compute_attendance_deductions', store=True)

    def _compute_lateness(self):
        for record in self:
            if record.employee_id and record.check_in:
                shift_start = record.employee_id.contract_id.resource_calendar_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(record.check_in.weekday())
                )
                if shift_start:
                    shift_start_time = datetime.combine(
                        record.check_in.date(),
                        (datetime.min + timedelta(hours=int(shift_start[0].hour_from), minutes=(shift_start[0].hour_from % 1) * 60)).time()
                    )

                    record.shift_start = shift_start_time
                    lateness = (record.check_in - shift_start_time).total_seconds() / 60
                    record.lateness = lateness if lateness > 0 else 0

    def _compute_attendance_deductions(self):
        hr_managers = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)])
        attendances = self.search([])
        # Attendance instead of recordgit .
        for attendance in attendances:
            employee = attendance.employee_id
            shift_start = employee.contract_id.resource_calendar_id.attendance_ids.filtered(
                lambda a: a.dayofweek == str(attendance.check_in.weekday())
            )
            
            shift_end = shift_start.mapped('hour_to')

            if not shift_start or not shift_end:
                continue

            shift_start_time = datetime.combine(
                attendance.check_in.date(), datetime.min.time()
            ) + timedelta(hours=shift_start[0].hour_from)

            shift_end_time = datetime.combine(
                attendance.check_in.date(), datetime.min.time()
            ) + timedelta(hours=int(shift_end[0]))

            attendance.shift_start = shift_start_time
            attendance.shift_end = shift_end_time

            lateness = attendance.lateness
            early_checkout = (shift_end_time - attendance.check_out).total_seconds() / 60 if attendance.check_out else None
            missing_checkout = attendance.check_out is None and (datetime.now() - shift_end_time).total_seconds() / 3600 >= 3

            deduction_amount = 0
            if lateness > 20:
                deduction_amount += (lateness - 20) * employee.per_minute_rate * employee.deduction_multiplier
            if early_checkout and early_checkout > 5:
                deduction_amount += (early_checkout - 5) * employee.per_minute_rate * employee.deduction_multiplier
            if missing_checkout:
                deduction_amount += (shift_end_time.hour * 60) * employee.per_minute_rate * employee.deduction_multiplier

            attendance.deduction_amount = deduction_amount

            if deduction_amount > 0:
                mail_template = self.env.ref('your_module.attendance_deduction_email_template')
                for manager in hr_managers:
                    mail_template.send_mail(manager.id, force_send=True)


    def _cron_compute_attendance_deductions(self):
        self._compute_attendance_deductions()
