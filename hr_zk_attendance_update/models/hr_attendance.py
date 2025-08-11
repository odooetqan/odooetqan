# -*- coding: utf-8 -*-
################################################################################
#   HR Attendance extensions: shift bounds, KPIs, and deductions
################################################################################
import logging
from datetime import datetime, timedelta

import pytz
from pytz import timezone, utc

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# ── Business rules ────────────────────────────────────────────────────────────
GRACE_LATE_MIN   = 30       # lateness grace (minutes)
GRACE_EARLY_MIN  = 15       # early checkout grace (minutes)
KSA_TZ = timezone('Asia/Riyadh')

# ── Helpers ───────────────────────────────────────────────────────────────────
def _to_utc_naive(dt_local, tz):
    """Local-aware -> UTC-naive (Odoo convention)."""
    if dt_local.tzinfo is None:
        aware = tz.localize(dt_local)
    else:
        aware = dt_local.astimezone(tz)
    return aware.astimezone(utc).replace(tzinfo=None)

def _build_day_shifts(calendar, day_date):
    """Return list of (start_utc_naive, end_utc_naive) for that day."""
    dwd = str(day_date.weekday())
    slots = []
    for att in calendar.attendance_ids.filtered(lambda a: a.dayofweek == dwd):
        start_local = datetime.combine(
            day_date,
            datetime.min.time().replace(
                hour=int(att.hour_from),
                minute=int((att.hour_from % 1) * 60),
                second=0
            )
        )
        end_local = datetime.combine(
            day_date,
            datetime.min.time().replace(
                hour=int(att.hour_to),
                minute=int((att.hour_to % 1) * 60),
                second=0
            )
        )
        slots.append((_to_utc_naive(start_local, KSA_TZ),
                      _to_utc_naive(end_local,   KSA_TZ)))
    # ensure morning before afternoon, etc.
    return sorted(slots, key=lambda s: s[0])


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Stored shift bounds (UTC-naive) for reporting
    shift_start = fields.Datetime(string='Shift Start', readonly=True)
    shift_end   = fields.Datetime(string='Shift End',   readonly=True)

    # KPIs
    notes = fields.Char('Notes')
    late_minutes = fields.Float(string="Lateness (Minutes)", compute="_compute_late_overtime_raw", store=True)
    overtime_minutes = fields.Float(string="Overtime (Minutes)", compute="_compute_late_overtime_raw", store=True)

    lateness = fields.Float(string="Lateness (minutes)", compute="_compute_attendance_metrics", store=True)
    early_checkout = fields.Float(string="Early Check-Out (minutes)", compute="_compute_attendance_metrics", store=True)
    shift_duration = fields.Float(string="Shift Duration (minutes)", compute="_compute_attendance_metrics", store=True)
    attended_duration = fields.Float(string="Attended Duration (minutes)", compute="_compute_attendance_metrics", store=True)
    attendance_gap = fields.Float(string="Attendance Gap (minutes)", compute="_compute_attendance_metrics", store=True)

    deduction_amount = fields.Float(
        string='Deduction Amount',
        compute='_compute_attendance_deductions',
        store=True
    )

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_recompute_attendance(self):
        for record in self:
            record._compute_attendance_metrics()
            record._compute_attendance_deductions()

    # ── Computes ──────────────────────────────────────────────────────────────
    @api.depends('employee_id', 'check_in', 'check_out')
    def _compute_late_overtime_raw(self):
        """
        Raw late/overtime without grace windows.
        Uses the shift that contains (or is nearest to) check_in.
        """
        for rec in self:
            rec.late_minutes = 0.0
            rec.overtime_minutes = 0.0
            if not rec.employee_id or not rec.check_in:
                continue

            cal = rec.employee_id.resource_calendar_id or rec.employee_id.contract_id.resource_calendar_id
            if not cal:
                continue

            shifts = _build_day_shifts(cal, rec.check_in.date())
            if not shifts:
                continue

            # choose the shift that contains check_in, else nearest boundary
            def _dist(s):
                s0, s1 = s
                if s0 <= rec.check_in <= s1:
                    return 0
                return min(abs((rec.check_in - s0).total_seconds()),
                           abs((rec.check_in - s1).total_seconds()))
            s_start, s_end = min(shifts, key=_dist)

            rec.shift_start = s_start
            rec.shift_end   = s_end

            # raw late
            rec.late_minutes = max(0.0, (rec.check_in - s_start).total_seconds()/60.0)

            # raw overtime (requires check_out)
            if rec.check_out:
                rec.overtime_minutes = max(0.0, (rec.check_out - s_end).total_seconds()/60.0)
            else:
                rec.overtime_minutes = 0.0

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_attendance_metrics(self):
        """
        KPIs with grace windows applied:
        - lateness:    max(0, late_minutes   - 30)
        - early_out:   max(0, early_minutes  - 15)
        """
        for rec in self:
            rec.lateness = rec.early_checkout = rec.shift_duration = rec.attended_duration = rec.attendance_gap = 0.0
            if not rec.check_in or not rec.employee_id:
                continue

            cal = rec.employee_id.resource_calendar_id or rec.employee_id.contract_id.resource_calendar_id
            if not cal:
                continue

            shifts = _build_day_shifts(cal, rec.check_in.date())
            if not shifts:
                continue

            # choose appropriate shift as above
            def _dist(s):
                s0, s1 = s
                if s0 <= rec.check_in <= s1:
                    return 0
                return min(abs((rec.check_in - s0).total_seconds()),
                           abs((rec.check_in - s1).total_seconds()))
            s_start, s_end = min(shifts, key=_dist)
            rec.shift_start = s_start
            rec.shift_end   = s_end

            # durations
            rec.shift_duration = (s_end - s_start).total_seconds()/60.0
            rec.attended_duration = ((rec.check_out or s_end) - rec.check_in).total_seconds()/60.0

            # lateness (with grace)
            raw_late = max(0.0, (rec.check_in - s_start).total_seconds()/60.0)
            rec.lateness = max(0.0, raw_late - GRACE_LATE_MIN)

            # early checkout (with grace)
            raw_early = 0.0
            if rec.check_out:
                raw_early = max(0.0, (s_end - rec.check_out).total_seconds()/60.0)
            rec.early_checkout = max(0.0, raw_early - GRACE_EARLY_MIN)

            rec.attendance_gap = rec.shift_duration - rec.attended_duration

    @api.depends(
        'check_in', 'check_out', 'employee_id',
        'employee_id.contract_id', 'employee_id.contract_id.resource_calendar_id.attendance_ids'
    )
    def _compute_attendance_deductions(self):
        """
        Sample monetary logic using per-minute rate & multiplier.
        Uses rec.lateness / early_checkout (already grace-adjusted).
        """
        for attendance in self:
            attendance.deduction_amount = 0.0

            if not attendance.employee_id or not attendance.check_in:
                continue

            emp = attendance.employee_id
            cal = emp.resource_calendar_id or emp.contract_id.resource_calendar_id
            if not cal:
                continue

            shifts = _build_day_shifts(cal, attendance.check_in.date())
            if not shifts:
                continue

            # choose same shift as KPIs
            def _dist(s):
                s0, s1 = s
                if s0 <= attendance.check_in <= s1:
                    return 0
                return min(abs((attendance.check_in - s0).total_seconds()),
                           abs((attendance.check_in - s1).total_seconds()))
            s_start, s_end = min(shifts, key=_dist)

            # store for reporting (UTC-naive)
            attendance.shift_start = s_start
            attendance.shift_end   = s_end

            per_minute_rate = getattr(emp, 'per_minute_rate', 0.0) or 0.0
            deduction_multiplier = getattr(emp, 'deduction_multiplier', 1.0) or 1.0

            # grace already applied in these two fields:
            late_after_grace   = attendance.lateness
            early_after_grace  = attendance.early_checkout

            deduction_amount = 0.0
            if late_after_grace > 0:
                deduction_amount += late_after_grace * per_minute_rate * deduction_multiplier
            if early_after_grace > 0:
                deduction_amount += early_after_grace * per_minute_rate * deduction_multiplier

            # Optional: missing checkout penalty (if no checkout 3h after shift end)
            if not attendance.check_out:
                if (fields.Datetime.now() - s_end).total_seconds() >= 3 * 3600:
                    # charge full remaining minutes of the shift
                    remaining = max(0.0, (s_end - attendance.check_in).total_seconds()/60.0)
                    deduction_amount += remaining * per_minute_rate * deduction_multiplier

            attendance.deduction_amount = deduction_amount

    # Optional cron wrapper
    def _cron_compute_attendance_deductions(self):
        self._compute_attendance_deductions()

# import datetime
# import logging
# import pytz
# from odoo import api, fields, models, _
# from odoo.exceptions import UserError, ValidationError
# from datetime import datetime, timedelta  # ✅ Ensure timedelta is imported
# from pytz import timezone, utc  # ✅ Import timezone functions
# from odoo import api, fields, models
# from datetime import datetime, timedelta

# class HrAttendance(models.Model):
#     _inherit = 'hr.attendance'

#     # lateness = fields.Float(string='Lateness (minutes)', compute='_compute_lateness', store=True)
#     shift_start = fields.Datetime(string='Shift Start')
#     shift_end = fields.Datetime(string='Shift End')
#     deduction_amount = fields.Float(string='Deduction Amount', compute='_compute_attendance_deductions', store=True)
#     notes = fields.Char('Notes')
#     late_minutes = fields.Float(string="Lateness (Minutes)", compute="_compute_lateness", store=True)
#     overtime_minutes = fields.Float(string="Overtime (Minutes)", compute="_compute_overtime", store=True)

#     lateness = fields.Float(string="Lateness (minutes)", compute="_compute_attendance_metrics", store=True)
#     early_checkout = fields.Float(string="Early Check-Out (minutes)", compute="_compute_attendance_metrics", store=True)
#     shift_duration = fields.Float(string="Shift Duration (minutes)", compute="_compute_attendance_metrics", store=True)
#     attended_duration = fields.Float(string="Attended Duration (minutes)", compute="_compute_attendance_metrics", store=True)
#     attendance_gap = fields.Float(string="Attendance Gap (minutes)", compute="_compute_attendance_metrics", store=True)


# # from odoo import api, fields, models
# # from datetime import datetime, timedelta

# # class HrAttendance(models.Model):
# #     _inherit = 'hr.attendance'

# #     lateness = fields.Float(string="Lateness (minutes)", compute="_compute_attendance_metrics", store=True)
# #     early_checkout = fields.Float(string="Early Check-Out (minutes)", compute="_compute_attendance_metrics", store=True)
# #     shift_duration = fields.Float(string="Shift Duration (minutes)", compute="_compute_attendance_metrics", store=True)
# #     attended_duration = fields.Float(string="Attended Duration (minutes)", compute="_compute_attendance_metrics", store=True)
# #     attendance_gap = fields.Float(string="Attendance Gap (minutes)", compute="_compute_attendance_metrics", store=True)

#     def action_recompute_attendance(self):
#         """ Manually trigger the computation of attendance metrics """
#         for record in self:
#             record._compute_attendance_metrics()

#     @api.depends('check_in', 'check_out', 'employee_id')
#     def _compute_attendance_metrics(self):
#         """ Compute lateness, early check-out, and durations """
#         for record in self:
#             if not record.check_in or not record.employee_id:
#                 continue

#             shift_start = shift_end = None
#             contract = record.employee_id.contract_id
#             if contract and contract.resource_calendar_id:
#                 shift = contract.resource_calendar_id.attendance_ids.filtered(lambda a: a.dayofweek == str(record.check_in.weekday()))
#                 if shift:
#                     # shift_start = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_from).seconds // 3600)
#                     # shift_end = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_to).seconds // 3600)


#                     shift_start = datetime.combine(
#                         record.check_in.date(),
#                         datetime.min.time().replace(
#                             hour=int(shift[0].hour_from),
#                             minute=int((shift[0].hour_from % 1) * 60),
#                             second=0
#                         )
#                     )

#                     shift_end = datetime.combine(
#                         record.check_in.date(),
#                         datetime.min.time().replace(
#                             hour=int(shift[0].hour_to),
#                             minute=int((shift[0].hour_to % 1) * 60),
#                             second=0
#                         )
#                     )
                    
#             # Calculate lateness and shift duration if shift_start is defined
#             if shift_start and record.check_in:
#                 record.lateness = max((record.check_in - shift_start).total_seconds() / 60, 0)
#                 record.shift_duration = (shift_end - shift_start).total_seconds() / 60 if shift_end else 0
#             else:
#                 record.lateness = 0
#                 record.shift_duration = 0

#             # Only calculate early checkout and attended duration if both check_in and check_out exist
#             if record.check_in and record.check_out and shift_end:
#                 record.early_checkout = max((shift_end - record.check_out).total_seconds() / 60, 0)
#                 record.attended_duration = (record.check_out - record.check_in).total_seconds() / 60
#             else:
#                 record.early_checkout = 0
#                 record.attended_duration = 0

#             # Calculate attendance gap only if both durations are available
#             if record.shift_duration and record.attended_duration:
#                 record.attendance_gap = record.shift_duration - record.attended_duration
#             else:
#                 record.attendance_gap = 0



#             # if shift_start:
#             #     record.lateness = max((record.check_in - shift_start).total_seconds() / 60, 0)
#             #     record.shift_duration = (shift_end - shift_start).total_seconds() / 60 if shift_end else 0
#             # else:
#             #     record.lateness = 0
#             #     record.shift_duration = 0

#             # if record.check_out and shift_end:
#             #     record.early_checkout = max((shift_end - record.check_out).total_seconds() / 60, 0)
#             #     record.attended_duration = (record.check_out - record.check_in).total_seconds() / 60
#             # else:
#             #     record.early_checkout = 0
#             #     record.attended_duration = 0

#             # record.attendance_gap = record.shift_duration - record.attended_duration

#     # @api.depends('check_in', 'check_out', 'employee_id')
#     # def _compute_attendance_metrics(self):
#     #     for record in self:
#     #         if not record.check_in or not record.employee_id:
#     #             continue

#     #         shift_start = shift_end = None
#     #         contract = record.employee_id.contract_id
#     #         if contract and contract.resource_calendar_id:
#     #             shift = contract.resource_calendar_id.attendance_ids.filtered(lambda a: a.dayofweek == str(record.check_in.weekday()))
#     #             if shift:
#     #                 shift_start = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_from).seconds // 3600)
#     #                 shift_end = datetime.combine(record.check_in.date(), timedelta(hours=shift[0].hour_to).seconds // 3600)

#     #         if shift_start:
#     #             record.lateness = max((record.check_in - shift_start).total_seconds() / 60, 0)
#     #             record.shift_duration = (shift_end - shift_start).total_seconds() / 60 if shift_end else 0
#     #         else:
#     #             record.lateness = 0
#     #             record.shift_duration = 0

#     #         if record.check_out and shift_end:
#     #             record.early_checkout = max((shift_end - record.check_out).total_seconds() / 60, 0)
#     #             record.attended_duration = (record.check_out - record.check_in).total_seconds() / 60
#     #         else:
#     #             record.early_checkout = 0
#     #             record.attended_duration = 0

#     #         record.attendance_gap = record.shift_duration - record.attended_duration

#     # @api.depends('employee_id', 'check_in')
#     # def _compute_lateness(self):
#     #     """Calculate lateness per shift in minutes."""
#     #     for record in self:
#     #         if not record.employee_id or not record.check_in:
#     #             record.late_minutes = 0
#     #             continue

#     #         shift = record.employee_id.resource_calendar_id
#     #         if not shift:
#     #             record.late_minutes = 0
#     #             continue

#     #         check_in_time = record.check_in
#     #         punch_date = check_in_time.date()
#     #         ksa_tz = timezone('Asia/Riyadh')

#     #         for att in shift.attendance_ids:
#     #             if att.dayofweek == str(punch_date.weekday()):
#     #                 shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
#     #                     hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60)
#     #                 )
#     #                 shift_start_utc = ksa_tz.localize(shift_start).astimezone(utc)

#     #                 # Calculate lateness per shift
#     #                 late_duration = (check_in_time.replace(tzinfo=None) - shift_start_utc.replace(tzinfo=None)).total_seconds() / 60
#     #                 record.late_minutes = max(0, late_duration)  # Ensure non-negative value



#     @api.depends('employee_id', 'check_in')
#     def _compute_lateness(self):
#         """Calculate lateness in minutes based on scheduled shift start time."""
#         for record in self:
#             if not record.employee_id or not record.check_in:
#                 record.late_minutes = 0
#                 continue

#             shift = record.employee_id.resource_calendar_id
#             if not shift:
#                 record.late_minutes = 0
#                 continue

#             check_in_time = record.check_in
#             punch_date = check_in_time.date()
#             ksa_tz = timezone('Asia/Riyadh')  # Adjust based on your timezone

#             for att in shift.attendance_ids:
#                 if att.dayofweek == str(punch_date.weekday()):
#                     shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
#                         hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60)
#                     )
#                     shift_start_utc = ksa_tz.localize(shift_start).astimezone(utc)

#                     late_duration = (check_in_time.replace(tzinfo=None) - shift_start_utc.replace(tzinfo=None)).total_seconds() / 60
#                     record.late_minutes = max(0, late_duration)  # Ensure non-negative value

#     @api.depends('employee_id', 'check_out')
#     def _compute_overtime(self):
#         """Calculate overtime in minutes based on scheduled shift end time."""
#         for record in self:
#             if not record.employee_id or not record.check_out:
#                 record.overtime_minutes = 0
#                 continue

#             shift = record.employee_id.resource_calendar_id
#             if not shift:
#                 record.overtime_minutes = 0
#                 continue

#             check_out_time = record.check_out
#             punch_date = check_out_time.date()
#             ksa_tz = timezone('Asia/Riyadh')

#             for att in shift.attendance_ids:
#                 if att.dayofweek == str(punch_date.weekday()):
#                     shift_end = datetime.combine(punch_date, datetime.min.time()).replace(
#                         hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60)
#                     )
#                     shift_end_utc = ksa_tz.localize(shift_end).astimezone(utc)

#                     overtime_duration = (check_out_time.replace(tzinfo=None) - shift_end_utc.replace(tzinfo=None)).total_seconds() / 60
#                     record.overtime_minutes = max(0, overtime_duration)


#     # def _compute_lateness(self):
#     #     for record in self:
#     #         if record.employee_id and record.check_in:
#     #             shift_start = record.employee_id.contract_id.resource_calendar_id.attendance_ids.filtered(
#     #                 lambda a: a.dayofweek == str(record.check_in.weekday())
#     #             )
#     #             if shift_start:
#     #                 from datetime import datetime, timedelta

#     #                 shift_start_time = datetime.combine(
#     #                     record.check_in.date(),
#     #                     (datetime.min + timedelta(hours=int(shift_start[0].hour_from), minutes=(shift_start[0].hour_from % 1) * 60)).time()
#     #                 )


#     #                 # shift_start_time = datetime.combine(record.check_in.date(),
#     #                 #                                      timedelta(hours=shift_start[0].hour_from).seconds // 3600)
#     #                 record.shift_start = shift_start_time
#     #                 lateness = (record.check_in - shift_start_time).total_seconds() / 60
#     #                 record.lateness = lateness if lateness > 0 else 0

#     @api.depends('check_in', 'check_out', 'employee_id', 'employee_id.contract_id', 'employee_id.contract_id.resource_calendar_id.attendance_ids')
#     def _compute_attendance_deductions(self):
#         hr_managers = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)])

#         for attendance in self:
#             employee = attendance.employee_id
#             shift_start_rec = employee.contract_id.resource_calendar_id.attendance_ids.filtered(
#                 lambda a: a.dayofweek == str(attendance.check_in.weekday())
#             )
#             shift_end_values = shift_start_rec.mapped('hour_to')
#             if not shift_start_rec or not shift_end_values:
#                 continue

#             # Calculate shift start time
#             shift_start_time = datetime.combine(attendance.check_in.date(), datetime.min.time()) \
#                             + timedelta(hours=shift_start_rec[0].hour_from)
#             # Calculate shift end time using the improved method:
#             shift_delta = timedelta(hours=shift_end_values[0])
#             shift_time = (datetime.min + shift_delta).time()
#             shift_end_time = datetime.combine(attendance.check_in.date(), shift_time)

#             attendance.shift_start = shift_start_time
#             attendance.shift_end = shift_end_time

#             # Calculate lateness, early checkout, and missing checkout
#             lateness = attendance.lateness
#             early_checkout = (shift_end_time - attendance.check_out).total_seconds() / 60 if attendance.check_out else None


#             # Ensure per_minute_rate and deduction_multiplier have default values
#             per_minute_rate = employee.per_minute_rate or 0
#             deduction_multiplier = employee.deduction_multiplier or 1

#             missing_checkout = attendance.check_out is None and (datetime.now() - shift_end_time).total_seconds() / 3600 >= 3

#             deduction_amount = 0
#             if lateness > 20:
#                 deduction_amount += (lateness - 20) * per_minute_rate * deduction_multiplier
#             if early_checkout and early_checkout > 5:
#                 deduction_amount += (early_checkout - 5) * per_minute_rate * deduction_multiplier
#             if missing_checkout:
#                 deduction_amount += (shift_end_time.hour * 60) * per_minute_rate * deduction_multiplier

#             attendance.deduction_amount = deduction_amount

#             # Consider moving email sending to a separate method
#             # if deduction_amount > 0:
#             #     mail_template = self.env.ref('hr_zk_attendance_update.attendance_deduction_email_template')
#             #     for manager in hr_managers:
#             #         mail_template.send_mail(manager.id, force_send=True)


#     def _cron_compute_attendance_deductions(self):
#         self._compute_attendance_deductions()
