# =========================
# models/hr_absence.py
# =========================
from datetime import datetime, timedelta, time as dtime
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Helper: get user's tz or fall back to Asia/Riyadh
def _tz(env):
    tzname = env.context.get("tz") or env.user.tz or "Asia/Riyadh"
    try:
        return pytz.timezone(tzname)
    except Exception:
        return pytz.timezone("Asia/Riyadh")

def _to_utc_naive(dt_local, tz):
    if dt_local.tzinfo is None:
        aware = tz.localize(dt_local)
    else:
        aware = dt_local.astimezone(tz)
    return aware.astimezone(pytz.utc).replace(tzinfo=None)

def _local_date_from_utc_naive(dt_utc_naive, tz):
    return pytz.utc.localize(dt_utc_naive).astimezone(tz).date()

def _day_bounds_utc(day, tz):
    start_local = datetime.combine(day, dtime.min)
    end_local = start_local + timedelta(days=1)
    return _to_utc_naive(start_local, tz), _to_utc_naive(end_local, tz)

def _build_day_shifts(calendar, day_date, tz):
    """Return list of (start_utc_naive, end_utc_naive) for that local day."""
    slots = []
    dwd = str(day_date.weekday())
    for att in calendar.attendance_ids.filtered(lambda a: a.dayofweek == dwd):
        start_local = datetime.combine(
            day_date,
            dtime(hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0),
        )
        end_local = datetime.combine(
            day_date,
            dtime(hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0),
        )
        slots.append((_to_utc_naive(start_local, tz), _to_utc_naive(end_local, tz)))
    return sorted(slots, key=lambda s: s[0])


class HrAttendanceDayline(models.Model):
    _name = "hr.attendance.dayline"
    _description = "Attendance Dayline (Present/Absent/Partial)"
    _order = "date desc, employee_id"

    employee_id = fields.Many2one("hr.employee", required=True, index=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True, index=True)
    date = fields.Date(required=True, index=True)

    # Shift window (UTC-naive) used to evaluate presence
    shift_start = fields.Datetime()
    shift_end = fields.Datetime()

    status = fields.Selection([
        ("present", "Present"),
        ("partial", "Partial"),
        ("absent", "Absent"),
    ], default="absent", index=True)

    attendance_id = fields.Many2one("hr.attendance", string="Linked Attendance")

    minutes_expected = fields.Float()
    minutes_attended = fields.Float()
    minutes_late = fields.Float()
    minutes_early = fields.Float()
    notes = fields.Char()

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, index=True
    )

    _sql_constraints = [
        ("uniq_day_emp_shift", "unique(employee_id, date, shift_start, shift_end)",
         "Dayline is already created for this day/shift."),
    ]

    @api.model
    def _attendance_domain_for_shift(self, employee, s_start, s_end):
        return [
            ("employee_id", "=", employee.id),
            ("check_in", "<", s_end),
            "|",
            ("check_out", "=", False),
            ("check_out", ">", s_start),
        ]

    @api.model
    def _company_partial_ratio(self):
        # Simple constant 0.5; switch to company config if you add settings later
        return 0.5

    @api.model
    def _compute_dayline_for(self, employee, day):
        tz = _tz(self.env)
        calendar = employee.resource_calendar_id or employee.contract_id.resource_calendar_id
        if not calendar:
            return []

        partial_ratio = self._company_partial_ratio()
        lines = []
        shifts = _build_day_shifts(calendar, day, tz)
        if not shifts:
            return []

        Att = self.env["hr.attendance"]

        for s_start, s_end in shifts:
            expected = (s_end - s_start).total_seconds() / 60.0
            att = Att.search(self._attendance_domain_for_shift(employee, s_start, s_end), limit=1)

            if not att:
                lines.append({
                    "employee_id": employee.id,
                    "date": day,
                    "shift_start": s_start,
                    "shift_end": s_end,
                    "status": "absent",
                    "attendance_id": False,
                    "minutes_expected": expected,
                    "minutes_attended": 0.0,
                    "minutes_late": 0.0,
                    "minutes_early": 0.0,
                    "notes": _("No attendance found for this shift"),
                })
                continue

            # Compute KPIs vs shift
            check_in = att.check_in
            check_out = att.check_out or s_end
            attended = max(0.0, (check_out - check_in).total_seconds() / 60.0)
            late = max(0.0, (check_in - s_start).total_seconds() / 60.0)
            early = max(0.0, (s_end - check_out).total_seconds() / 60.0) if att.check_out else 0.0

            status = "present"
            if attended <= 0.0:
                status = "absent"
            elif attended < (partial_ratio * expected):
                status = "partial"

            lines.append({
                "employee_id": employee.id,
                "date": day,
                "shift_start": s_start,
                "shift_end": s_end,
                "status": status,
                "attendance_id": att.id,
                "minutes_expected": expected,
                "minutes_attended": attended,
                "minutes_late": late,
                "minutes_early": early,
                "notes": att.notes or False,
            })
        return lines

    # Public entrypoints -------------------------------------------------
    @api.model
    def build_for_range(self, date_from, date_to, employees=None):
        """Recompute daylines for a given local date range (inclusive)."""
        if isinstance(date_from, str):
            date_from = fields.Date.from_string(date_from)
        if isinstance(date_to, str):
            date_to = fields.Date.from_string(date_to)

        Emp = self.env["hr.employee"]
        if employees is None:
            employees = Emp.search([])
        elif isinstance(employees, models.Model):
            pass  # recordset
        else:
            employees = Emp.browse(employees)

        # simple: drop existing rows in range (per employee) then recreate
        self.search([("date", ">=", date_from), ("date", "<=", date_to)]).unlink()

        all_vals = []
        for emp in employees:
            day = date_from
            while day <= date_to:
                all_vals += self._compute_dayline_for(emp, day)
                day += timedelta(days=1)

        if all_vals:
            self.create(all_vals)
        return True

    @api.model
    def cron_build_yesterday(self):
        tz = _tz(self.env)
        today_local = pytz.utc.localize(fields.Datetime.now()).astimezone(tz).date()
        target_day = today_local - timedelta(days=1)
        self.build_for_range(target_day, target_day)


# Light extension on hr.employee for a smart button ---------------------------
class HrEmployee(models.Model):
    _inherit = "hr.employee"

    absence_day_count = fields.Integer(
        string="Absent Days (last 30d)", compute="_compute_absence_day_count"
    )

    def _compute_absence_day_count(self):
        Day = self.env["hr.attendance.dayline"]
        today = fields.Date.context_today(self)
        since = today - timedelta(days=30)
        for emp in self:
            emp.absence_day_count = Day.search_count([
                ("employee_id", "=", emp.id),
                ("date", ">=", since),
                ("status", "=", "absent"),
            ])

    def action_open_daylines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attendance Daylines"),
            "res_model": "hr.attendance.dayline",
            "view_mode": "tree,graph,pivot,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"search_default_this_month": 1},
        }


# Optional: extend hr.attendance list with a related helper column -------------
class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    day_status = fields.Selection([
        ("present", "Present"),
        ("partial", "Partial"),
        ("absent", "Absent"),
    ], string="Day Status", compute="_compute_day_status", store=False)
    
    shift_start = fields.Datetime(string="Shift Start", readonly=True)
    shift_end   = fields.Datetime(string="Shift End", readonly=True)
    day_status  = fields.Selection([
        ("present", "Present"),
        ("partial", "Partial"),
        ("absent", "Absent"),
    ], string="Day Status", compute="_compute_day_status", store=False)
    


    # Keep these only if you plan to write them from your biometric pipeline



    # def _compute_day_status(self):
    #     Day = self.env["hr.attendance.dayline"]
    #     tz = _tz(self.env)
    #     for att in self:
    #         att.day_status = False
    #         if not att.employee_id or not att.check_in:
    #             continue
    #         local_day = _local_date_from_utc_naive(att.check_in, tz)
    #         domain = [("employee_id", "=", att.employee_id.id), ("date", "=", local_day)]
    #         # Prefer exact shift match if you store shift_start/end on attendance
    #         if att.shift_start and att.shift_end:
    #             domain += [("shift_start", "=", att.shift_start), ("shift_end", "=", att.shift_end)]
    #         dl = Day.search(domain, limit=1)
    #         att.day_status = dl.status if dl else False

    def _compute_day_status(self):
        Day = self.env["hr.attendance.dayline"]
        tz = _tz(self.env)
        for att in self:
            if not att.employee_id or not att.check_in:
                att.day_status = False
                continue
            local_day = _local_date_from_utc_naive(att.check_in, tz)
            s_start = att.shift_start or False
            s_end = att.shift_end or False
            domain = [("employee_id", "=", att.employee_id.id), ("date", "=", local_day)]
            if s_start and s_end:
                domain += [("shift_start", "=", s_start), ("shift_end", "=", s_end)]
            dl = Day.search(domain, limit=1)
            att.day_status = dl.status if dl else False
