from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        """ Calculates salary deductions before finalizing payslip """
        for payslip in self:
            contract = payslip.contract_id
            daily_salary = contract.wage / 30  # Assuming 30 days in a month
            hourly_salary = daily_salary / 8  # Assuming 8 hours per day

            attendances = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', payslip.employee_id.id),
                ('check_in', '>=', payslip.date_from),
                ('check_out', '<=', payslip.date_to),
            ])

            for attendance in attendances:
                shift = self.env['resource.calendar.attendance'].sudo().search([
                    ('calendar_id', '=', contract.resource_calendar_id.id),
                    ('dayofweek', '=', str(attendance.check_in.weekday()))
                ], limit=1)

                shift_start = attendance.check_in.replace(hour=int(shift.hour_from))
                shift_end = attendance.check_in.replace(hour=int(shift.hour_to))

                late_minutes = max(0, (attendance.check_in - shift_start).total_seconds() / 60)
                early_leave_minutes = max(0, (shift_end - attendance.check_out).total_seconds() / 60)

                absent = late_minutes > 120 or early_leave_minutes > 120  # Absent if more than 2 hours late

                self.env['hr.discount'].create({
                    'employee_id': payslip.employee_id.id,
                    'date': attendance.check_in.date(),
                    'shift_start': shift_start,
                    'shift_end': shift_end,
                    'check_in': attendance.check_in,
                    'check_out': attendance.check_out,
                    'late_minutes': late_minutes,
                    'early_leave_minutes': early_leave_minutes,
                    'absent': absent,
                    'daily_salary': daily_salary,
                    'hourly_salary': hourly_salary,
                })
        super(HrPayslip, self).compute_sheet()
