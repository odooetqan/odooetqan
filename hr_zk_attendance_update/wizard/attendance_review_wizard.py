# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta

class AttendanceReviewWizard(models.TransientModel):
    _name = 'attendance.review.wizard'
    _description = 'Review Attendance from Biometric Buffer'

    employee_id   = fields.Many2one('hr.employee', string="Employee", required=True)
    date_from     = fields.Datetime(string="From", required=True)
    date_to       = fields.Datetime(string="To", required=True)
    window_min    = fields.Integer(string="Window (± minutes)", default=20)
    include_processed = fields.Boolean(string="Include processed buffer logs", default=False)
    dry_run       = fields.Boolean(string="Dry run (don’t write yet)", default=False)
    line_ids      = fields.One2many('attendance.review.wizard.line', 'wizard_id', string="Suggestions")
    note          = fields.Html(string="Notes", sanitize=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Context helpers: coming from hr.attendance form or hr.employee
        emp = self.env.context.get('default_employee_id') or self.env.context.get('employee_id')
        if emp:
            res.setdefault('employee_id', emp)
        # If coming from an attendance record, prefill range = that day [00:00, 23:59:59]
        att_id = self.env.context.get('active_id') if self.env.context.get('active_model') == 'hr.attendance' else False
        if att_id:
            att = self.env['hr.attendance'].browse(att_id)
            day0 = fields.Datetime.to_datetime(str(att.check_in.date()))  # 00:00
            day1 = day0 + timedelta(days=1, seconds=-1)                   # 23:59:59
            res.update({'date_from': day0, 'date_to': day1})
        else:
            now = fields.Datetime.now()
            res.setdefault('date_from', now.replace(hour=0, minute=0, second=0, microsecond=0))
            res.setdefault('date_to',   now.replace(hour=23, minute=59, second=59, microsecond=0))
        return res

    def _iter_days(self, d0, d1):
        cur = d0.date()
        last = d1.date()
        while cur <= last:
            yield cur
            cur += timedelta(days=1)

    def action_scan(self):
        """Build suggestion lines per shift using your same pairing rules."""
        self.ensure_one()
        Line = self.env['attendance.review.wizard.line']
        Line.search([('wizard_id', '=', self.id)]).unlink()

        emp = self.employee_id
        cal = emp.resource_calendar_id or emp.contract_id.resource_calendar_id
        if not cal:
            self.note = _("<p><b>No working calendar on employee/contract.</b></p>")
            return

        # Collect buffer punches for this employee & range
        domain = [
            ('employee_id', '=', emp.id),
            ('punching_time', '>=', self.date_from),
            ('punching_time', '<=', self.date_to),
        ]
        if not self.include_processed:
            domain.append(('processed', '=', False))
        buf = self.env['zk.machine.attendance'].search(domain, order='punching_time asc')

        # Bucket: { date: [datetime, ...] } (UTC-naive already)
        by_day = {}
        for r in buf:
            dt = fields.Datetime.from_string(r.punching_time).replace(tzinfo=None)
            by_day.setdefault(dt.date(), []).append((dt, r))

        # Use your helpers from the main module:
        # _build_day_shifts(calendar, day_date) and _safe_create_attendance on buffer model
        # We’ll call _safe_create_attendance through the buffer model (self.env['zk.machine.attendance'])
        BufModel = self.env['zk.machine.attendance']

        suggestion_count = 0
        for day in self._iter_days(self.date_from, self.date_to):
            shifts = self.env['zk.machine.attendance']._build_day_shifts(cal, day) if hasattr(BufModel, '_build_day_shifts') else None
            # Fallback: import from module namespace if not bound; but in your code _build_day_shifts is defined at module top.
            if not shifts:
                from odoo.addons.<your_module_name>.models import biometric_attendance  # adjust path if needed
                shifts = biometric_attendance._build_day_shifts(cal, day)

            day_points = [p for (p, _r) in by_day.get(day, [])]
            punch_map  = {p: r for (p, r) in by_day.get(day, [])}
            for (s_start, s_end) in shifts:
                start_win = s_start - timedelta(minutes=self.window_min)
                end_win   = s_end   + timedelta(minutes=self.window_min)
                near = [p for p in day_points if start_win <= p <= end_win]
                near.sort()
                punch_cnt = len(near)

                check_in = check_out = False
                rule = ''
                if punch_cnt >= 2:
                    check_in, check_out = near[0], near[-1]
                    rule = 'first/last'
                elif punch_cnt == 1:
                    only = near[0]
                    # mirror your pairing rule
                    if abs((only - s_start).total_seconds()) <= abs((only - s_end).total_seconds()):
                        check_in = only
                        check_out = s_end - timedelta(hours=1)
                        rule = 'single near start'
                    else:
                        check_in = s_start + timedelta(hours=1)
                        check_out = only
                        rule = 'single near end'
                else:
                    # nothing near this shift; still show an empty line to help review
                    Line.create({
                        'wizard_id': self.id,
                        'day': day,
                        'shift_start': s_start,
                        'shift_end': s_end,
                        'punch_count': 0,
                        'punches': '',
                        'suggested_in': False,
                        'suggested_out': False,
                        'action': 'skip',
                        'reason': 'No punches within window',
                    })
                    continue

                # Build a compact punches string
                punches_str = ', '.join([p.strftime('%H:%M:%S') for p in near])

                # Detect overlapping existing attendance for info
                overlapping = self.env['hr.attendance'].search([
                    ('employee_id', '=', emp.id),
                    ('check_in', '<', (check_out or s_end) or s_end),
                    '|',
                    ('check_out', '=', False),
                    ('check_out', '>', (check_in or s_start) or s_start),
                ], limit=1)
                action = 'create' if not overlapping else 'adjust'

                Line.create({
                    'wizard_id': self.id,
                    'day': day,
                    'shift_start': s_start,
                    'shift_end': s_end,
                    'punch_count': punch_cnt,
                    'punches': punches_str,
                    'suggested_in': check_in,
                    'suggested_out': check_out,
                    'existing_attendance_id': overlapping.id or False,
                    'action': action,
                    'reason': rule,
                })
                suggestion_count += 1

        self.note = _("<p>Scan finished. Suggestions: <b>%s</b>. Adjust <i>Action</i> per line, then Apply.</p>") % suggestion_count

    def action_apply(self):
        self.ensure_one()
        BufModel = self.env['zk.machine.attendance']
        applied = 0
        for line in self.line_ids:
            if line.action == 'skip' or not line.suggested_in:
                continue
            if self.dry_run:
                applied += 1
                continue

            # Use the safe creator you added on the buffer model
            if hasattr(BufModel, '_safe_create_attendance'):
                created = BufModel._safe_create_attendance(self.employee_id, line.suggested_in, line.suggested_out)
            else:
                # fallback minimal create (should not happen in your module)
                created = self.env['hr.attendance'].create({
                    'employee_id': self.employee_id.id,
                    'check_in':  line.suggested_in,
                    'check_out': line.suggested_out or (line.suggested_in + timedelta(minutes=1)),
                })

            # mark used buffer punches as processed
            start_win = line.shift_start - timedelta(minutes=self.window_min)
            end_win   = line.shift_end   + timedelta(minutes=self.window_min)
            buf = self.env['zk.machine.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('punching_time', '>=', start_win),
                ('punching_time', '<=', end_win),
            ])
            buf.write({'processed': True})
            applied += 1

        self.note = _("<p>Applied lines: <b>%s</b>.</p>") % applied
        # reopen the wizard to show final note
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.review.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class AttendanceReviewWizardLine(models.TransientModel):
    _name = 'attendance.review.wizard.line'
    _description = 'Attendance Review Suggestion Line'

    wizard_id   = fields.Many2one('attendance.review.wizard', required=True, ondelete='cascade')
    day         = fields.Date(string="Day")
    shift_start = fields.Datetime(string="Shift Start", readonly=True)
    shift_end   = fields.Datetime(string="Shift End", readonly=True)
    punch_count = fields.Integer(string="#Punches", readonly=True)
    punches     = fields.Char(string="Punches (HH:MM:SS)", readonly=True)
    suggested_in  = fields.Datetime(string="Suggested In")
    suggested_out = fields.Datetime(string="Suggested Out")
    existing_attendance_id = fields.Many2one('hr.attendance', string="Existing")
    action = fields.Selection([
        ('create', 'Create'),
        ('adjust', 'Adjust/Close Open'),
        ('skip',   'Skip'),
    ], default='create', string="Action")
    reason = fields.Char(string="Rule/Reason")
