
import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta  # ✅ Ensure timedelta is imported
from pytz import timezone, utc  # ✅ Import timezone functions
from odoo import api, fields, models
from datetime import datetime, timedelta

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # lateness = fields.Float(string='Lateness (minutes)', compute='_compute_lateness', store=True)
    shift_start = fields.Datetime(string='Shift Start')
    shift_end = fields.Datetime(string='Shift End')
    deduction_amount = fields.Float(string='Deduction Amount', compute='_compute_attendance_deductions', store=True)
    notes = fields.Char('Notes')
    late_minutes = fields.Float(string="Lateness (Minutes)", compute="_compute_lateness", store=True)
    overtime_minutes = fields.Float(string="Overtime (Minutes)", compute="_compute_overtime", store=True)

    lateness = fields.Float(string="Lateness (minutes)", compute="_compute_attendance_metrics", store=True)
    early_checkout = fields.Float(string="Early Check-Out (minutes)", compute="_compute_attendance_metrics", store=True)
    shift_duration = fields.Float(string="Shift Duration (minutes)", compute="_compute_attendance_metrics", store=True)
    attended_duration = fields.Float(string="Attended Duration (minutes)", compute="_compute_attendance_metrics", store=True)
    attendance_gap = fields.Float(string="Attendance Gap (minutes)", compute="_compute_attendance_metrics", store=True)


# from odoo import api, fields, models
# from datetime import datetime, timedelta

# class HrAttendance(models.Model):
#     _inherit = 'hr.attendance'

#     lateness = fields.Float(string="Lateness (minutes)", compute="_compute_attendance_metrics", store=True)
#     early_checkout = fields.Float(string="Early Check-Out (minutes)", compute="_compute_attendance_metrics", store=True)
#     shift_duration = fields.Float(string="Shift Duration (minutes)", compute="_compute_attendance_metrics", store=True)
#     attended_duration = fields.Float(string="Attended Duration (minutes)", compute="_compute_attendance_metrics", store=True)
#     attendance_gap = fields.Float(string="Attendance Gap (minutes)", compute="_compute_attendance_metrics", store=True)

    def action_recompute_attendance(self):
        """ Manually trigger the computation of attendance metrics """
        for record in self:
            record._compute_attendance_metrics()

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_attendance_metrics(self):
        """ Compute lateness, early check-out, and durations """
        for record in self:
            if not record.check_in or not record.employee_id:
                continue

            shift_start = shift_end = None
            contract = record.employee_id.contract_id
            if contract and contract.resource_calendar_id:
                shift = contract.resource_calendar_id.attendance_ids.filtered(lambda a: a.dayofweek == str(record.check_in.weekday()))
                if shift:
                    # shift_start = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_from).seconds // 3600)
                    # shift_end = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_to).seconds // 3600)


                    shift_start = datetime.combine(
                        record.check_in.date(),
                        datetime.min.time().replace(
                            hour=int(shift[0].hour_from),
                            minute=int((shift[0].hour_from % 1) * 60),
                            second=0
                        )
                    )

                    shift_end = datetime.combine(
                        record.check_in.date(),
                        datetime.min.time().replace(
                            hour=int(shift[0].hour_to),
                            minute=int((shift[0].hour_to % 1) * 60),
                            second=0
                        )
                    )



            if shift_start:
                record.lateness = max((record.check_in - shift_start).total_seconds() / 60, 0)
                record.shift_duration = (shift_end - shift_start).total_seconds() / 60 if shift_end else 0
            else:
                record.lateness = 0
                record.shift_duration = 0

            if record.check_out and shift_end:
                record.early_checkout = max((shift_end - record.check_out).total_seconds() / 60, 0)
                record.attended_duration = (record.check_out - record.check_in).total_seconds() / 60
            else:
                record.early_checkout = 0
                record.attended_duration = 0

            record.attendance_gap = record.shift_duration - record.attended_duration

    # @api.depends('check_in', 'check_out', 'employee_id')
    # def _compute_attendance_metrics(self):
    #     for record in self:
    #         if not record.check_in or not record.employee_id:
    #             continue

    #         shift_start = shift_end = None
    #         contract = record.employee_id.contract_id
    #         if contract and contract.resource_calendar_id:
    #             shift = contract.resource_calendar_id.attendance_ids.filtered(lambda a: a.dayofweek == str(record.check_in.weekday()))
    #             if shift:
    #                 shift_start = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_from).seconds // 3600)
    #                 shift_end = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_to).seconds // 3600)

    #         if shift_start:
    #             record.lateness = max((record.check_in - shift_start).total_seconds() / 60, 0)
    #             record.shift_duration = (shift_end - shift_start).total_seconds() / 60 if shift_end else 0
    #         else:
    #             record.lateness = 0
    #             record.shift_duration = 0

    #         if record.check_out and shift_end:
    #             record.early_checkout = max((shift_end - record.check_out).total_seconds() / 60, 0)
    #             record.attended_duration = (record.check_out - record.check_in).total_seconds() / 60
    #         else:
    #             record.early_checkout = 0
    #             record.attended_duration = 0

    #         record.attendance_gap = record.shift_duration - record.attended_duration

    # @api.depends('employee_id', 'check_in')
    # def _compute_lateness(self):
    #     """Calculate lateness per shift in minutes."""
    #     for record in self:
    #         if not record.employee_id or not record.check_in:
    #             record.late_minutes = 0
    #             continue

    #         shift = record.employee_id.resource_calendar_id
    #         if not shift:
    #             record.late_minutes = 0
    #             continue

    #         check_in_time = record.check_in
    #         punch_date = check_in_time.date()
    #         ksa_tz = timezone('Asia/Riyadh')

    #         for att in shift.attendance_ids:
    #             if att.dayofweek == str(punch_date.weekday()):
    #                 shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
    #                     hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60)
    #                 )
    #                 shift_start_utc = ksa_tz.localize(shift_start).astimezone(utc)

    #                 # Calculate lateness per shift
    #                 late_duration = (check_in_time.replace(tzinfo=None) - shift_start_utc.replace(tzinfo=None)).total_seconds() / 60
    #                 record.late_minutes = max(0, late_duration)  # Ensure non-negative value



    @api.depends('employee_id', 'check_in')
    def _compute_lateness(self):
        """Calculate lateness in minutes based on scheduled shift start time."""
        for record in self:
            if not record.employee_id or not record.check_in:
                record.late_minutes = 0
                continue

            shift = record.employee_id.resource_calendar_id
            if not shift:
                record.late_minutes = 0
                continue

            check_in_time = record.check_in
            punch_date = check_in_time.date()
            ksa_tz = timezone('Asia/Riyadh')  # Adjust based on your timezone

            for att in shift.attendance_ids:
                if att.dayofweek == str(punch_date.weekday()):
                    shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
                        hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60)
                    )
                    shift_start_utc = ksa_tz.localize(shift_start).astimezone(utc)

                    late_duration = (check_in_time.replace(tzinfo=None) - shift_start_utc.replace(tzinfo=None)).total_seconds() / 60
                    record.late_minutes = max(0, late_duration)  # Ensure non-negative value

    @api.depends('employee_id', 'check_out')
    def _compute_overtime(self):
        """Calculate overtime in minutes based on scheduled shift end time."""
        for record in self:
            if not record.employee_id or not record.check_out:
                record.overtime_minutes = 0
                continue

            shift = record.employee_id.resource_calendar_id
            if not shift:
                record.overtime_minutes = 0
                continue

            check_out_time = record.check_out
            punch_date = check_out_time.date()
            ksa_tz = timezone('Asia/Riyadh')

            for att in shift.attendance_ids:
                if att.dayofweek == str(punch_date.weekday()):
                    shift_end = datetime.combine(punch_date, datetime.min.time()).replace(
                        hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60)
                    )
                    shift_end_utc = ksa_tz.localize(shift_end).astimezone(utc)

                    overtime_duration = (check_out_time.replace(tzinfo=None) - shift_end_utc.replace(tzinfo=None)).total_seconds() / 60
                    record.overtime_minutes = max(0, overtime_duration)


    # def _compute_lateness(self):
    #     for record in self:
    #         if record.employee_id and record.check_in:
    #             shift_start = record.employee_id.contract_id.resource_calendar_id.attendance_ids.filtered(
    #                 lambda a: a.dayofweek == str(record.check_in.weekday())
    #             )
    #             if shift_start:
    #                 from datetime import datetime, timedelta

    #                 shift_start_time = datetime.combine(
    #                     record.check_in.date(),
    #                     (datetime.min + timedelta(hours=int(shift_start[0].hour_from), minutes=(shift_start[0].hour_from % 1) * 60)).time()
    #                 )


    #                 # shift_start_time = datetime.combine(record.check_in.date(),
    #                 #                                      timedelta(hours=shift_start[0].hour_from).seconds // 3600)
    #                 record.shift_start = shift_start_time
    #                 lateness = (record.check_in - shift_start_time).total_seconds() / 60
    #                 record.lateness = lateness if lateness > 0 else 0

    @api.depends('check_in', 'check_out', 'employee_id', 'employee_id.contract_id', 'employee_id.contract_id.resource_calendar_id.attendance_ids')
    def _compute_attendance_deductions(self):
        hr_managers = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)])

        for attendance in self:
            employee = attendance.employee_id
            shift_start_rec = employee.contract_id.resource_calendar_id.attendance_ids.filtered(
                lambda a: a.dayofweek == str(attendance.check_in.weekday())
            )
            shift_end_values = shift_start_rec.mapped('hour_to')
            if not shift_start_rec or not shift_end_values:
                continue

            # Calculate shift start time
            shift_start_time = datetime.combine(attendance.check_in.date(), datetime.min.time()) \
                            + timedelta(hours=shift_start_rec[0].hour_from)
            # Calculate shift end time using the improved method:
            shift_delta = timedelta(hours=shift_end_values[0])
            shift_time = (datetime.min + shift_delta).time()
            shift_end_time = datetime.combine(attendance.check_in.date(), shift_time)

            attendance.shift_start = shift_start_time
            attendance.shift_end = shift_end_time

            # Calculate lateness, early checkout, and missing checkout
            lateness = attendance.lateness
            early_checkout = (shift_end_time - attendance.check_out).total_seconds() / 60 if attendance.check_out else None


            # Ensure per_minute_rate and deduction_multiplier have default values
            per_minute_rate = employee.per_minute_rate or 0
            deduction_multiplier = employee.deduction_multiplier or 1

            missing_checkout = attendance.check_out is None and (datetime.now() - shift_end_time).total_seconds() / 3600 >= 3

            deduction_amount = 0
            if lateness > 20:
                deduction_amount += (lateness - 20) * employee.per_minute_rate * employee.deduction_multiplier
            if early_checkout and early_checkout > 5:
                deduction_amount += (early_checkout - 5) * employee.per_minute_rate * employee.deduction_multiplier
            if missing_checkout:
                deduction_amount += (shift_end_time.hour * 60) * employee.per_minute_rate * employee.deduction_multiplier

            attendance.deduction_amount = deduction_amount

            # Consider moving email sending to a separate method
            # if deduction_amount > 0:
            #     mail_template = self.env.ref('hr_zk_attendance_update.attendance_deduction_email_template')
            #     for manager in hr_managers:
            #         mail_template.send_mail(manager.id, force_send=True)


    def _cron_compute_attendance_deductions(self):
        self._compute_attendance_deductions()

