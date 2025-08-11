# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies
#    (https://www.cybrosys.com).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#
################################################################################
import logging
import pytz
from datetime import datetime, timedelta
from pytz import timezone, utc
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")

# ── Business rules ────────────────────────────────────────────────────────────
GRACE_LATE_MIN   = 30       # lateness grace (minutes)
GRACE_EARLY_MIN  = 15       # early checkout grace (minutes)
AUTOCHECKOUT_HRS = 1        # auto-checkout 1h before shift end when no out punch
NO_PUNCH_WINDOW  = 20       # consider punches within ± window minutes around shift
KSA_TZ = timezone('Asia/Riyadh')


# ── Helpers (module-level) ────────────────────────────────────────────────────
def _to_utc_naive(dt_local, tz):
    """Local aware -> UTC naive (Odoo convention)."""
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
    return sorted(slots, key=lambda s: s[0])

def _group_unprocessed_punches(env):
    """{(device_id, date): [(punch_dt, record), ...]} for unprocessed only."""
    by_emp_day = {}
    recs = env['zk.machine.attendance'].search([('processed', '=', False)], order='punching_time asc')
    for r in recs:
        p = fields.Datetime.from_string(r.punching_time).replace(tzinfo=None)  # UTC naive from DB
        key = (r.device_id_num, p.date())
        by_emp_day.setdefault(key, []).append((p, r))
    return by_emp_day


# ── Device config model ───────────────────────────────────────────────────────
class BiometricDeviceDetails(models.Model):
    """Model for configuring and connecting the biometric device with Odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', required=True, help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', required=True, help="The Port Number of the Device")
    address_id = fields.Many2one('res.partner', string='Working Address', help='Working address of the partner')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id.id, help='Current Company')

    def device_connect(self, zk):
        try:
            return zk.connect()
        except Exception as e:
            _logger.error("Connection error: %s", e)
            return False

    def action_test_connection(self):
        zk = ZK(self.device_ip, port=self.port_number, timeout=30, password=False, ommit_ping=False)
        try:
            if zk.connect():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'message': 'Successfully Connected', 'type': 'success', 'sticky': False}
                }
        except Exception as error:
            raise ValidationError(f'{error}')

    def action_set_timezone(self):
        """Set current user timezone time to device."""
        for info in self:
            try:
                zk = ZK(info.device_ip, port=info.port_number, timeout=15, password=0, force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if not conn:
                raise UserError(_("Please Check the Connection"))
            user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
            user_now = pytz.utc.localize(fields.Datetime.now()).astimezone(pytz.timezone(user_tz))
            conn.set_time(user_now)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'message': 'Successfully Set the Time', 'type': 'success', 'sticky': False}
            }

    def action_clear_attendance(self):
        """Clear device log + Odoo buffer table."""
        for info in self:
            try:
                zk = ZK(info.device_ip, port=info.port_number, timeout=30, password=0, force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(_("Please install it with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if not conn:
                raise UserError(_('Unable to connect to Attendance Device. Please use Test Connection button to verify.'))
            conn.enable_device()
            if zk.get_attendance():
                conn.clear_attendance()
                self._cr.execute("DELETE FROM zk_machine_attendance")
                conn.disconnect()
            else:
                raise UserError(_('Unable to clear Attendance log. Are you sure the attendance log is not empty?'))

    @api.model
    def cron_download(self):
        for machine in self.search([]):
            machine.action_download_attendance()

    def action_restart_device(self):
        zk = ZK(self.device_ip, port=self.port_number, timeout=15, password=0, force_udp=False, ommit_ping=False)
        self.device_connect(zk).restart()

    def action_download_attendance(self):
        """Download attendance and store in buffer table `zk.machine.attendance`."""
        _logger.info("++++++++++++ Cron Executed: download ++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        # fetch all, or set a date window if you like:
        start_date = datetime(2023, 1, 1)

        for info in self:
            try:
                zk = ZK(info.device_ip, port=info.port_number, timeout=15, password=0, force_udp=False, ommit_ping=False)
            except NameError:
                _logger.error("Pyzk module not found! pip3 install pyzk")
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

            conn = self.device_connect(zk)
            self.action_set_timezone()
            if not conn:
                _logger.error("Unable to connect, check network.")
                raise UserError(_('Unable to connect, please check the network connections.'))

            conn.disable_device()
            attendance_list = conn.get_attendance() or []
            _logger.info("Retrieved %s records from device.", len(attendance_list))

            for each in attendance_list:
                if each.timestamp < start_date:
                    continue

                # device returns local timestamp (device TZ) -> convert to UTC naive
                local_tz = pytz.timezone(self.env.user.partner_id.tz or 'Asia/Riyadh')
                local_dt = local_tz.localize(each.timestamp, is_dst=None)
                utc_dt   = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
                atten_time = fields.Datetime.to_string(utc_dt)

                employee = self.env['hr.employee'].search([('device_id_num', '=', each.user_id)], limit=1)
                if not employee:
                    _logger.warning("No Employee for Device ID %s", each.user_id)
                    continue

                # unique by device_id_num + punching_time
                dup = zk_attendance.search([
                    ('device_id_num', '=', each.user_id),
                    ('punching_time', '=', atten_time),
                ], limit=1)
                if dup:
                    continue

                zk_attendance.create({
                    'employee_id': employee.id,
                    'device_id_num': each.user_id,
                    'attendance_type': str(each.status),
                    'punch_type': str(each.punch),
                    'punching_time': atten_time,
                    'address_id': info.address_id.id,
                })

            conn.disconnect()
        return True


# ── Buffer (intermediate) model ───────────────────────────────────────────────
class MachineAttendance(models.Model):
    """Intermediate table to store biometric attendance before processing."""
    _name = 'zk.machine.attendance'
    _description = 'Biometric Attendance Log'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    device_id_num = fields.Char(string="Device ID", required=True)
    punching_time = fields.Datetime(string="Punching Time", required=True)  # UTC naive
    address_id = fields.Many2one('res.partner', string="Location", default=lambda self: self._default_address_id)
    processed = fields.Boolean(string="Processed", default=False)
    attendance_type = fields.Selection([('0', 'Check In'), ('1', 'Check Out')], string="Attendance Type", required=True)
    punch_type = fields.Char(string="Punch Type")

    @api.model
    def _default_address_id(self):
        company = self.env.company
        return company.partner_id.id if company.partner_id else False

    def action_process_attendance_manual(self):
        self.action_process_attendance()

    def action_process_attendance(self):
        """
        Build hr.attendance per shift:
        - multiple punches: first->in, last->out
        - single punch near start: in=punch, out=shift_end-1h
          single punch near end:   in=shift_start+1h, out=punch
        - mark used punches as processed
        """
        hr_att = self.env['hr.attendance']
        grouped = _group_unprocessed_punches(self.env)

        for (dev_id, day), punches in grouped.items():
            employee = self.env['hr.employee'].search([('device_id_num', '=', dev_id)], limit=1)
            if not employee or not (employee.resource_calendar_id or employee.contract_id.resource_calendar_id):
                continue
            calendar = employee.resource_calendar_id or employee.contract_id.resource_calendar_id

            shifts = _build_day_shifts(calendar, day)
            if not shifts:
                continue

            times_only = [p for (p, _r) in punches]
            punch_map  = {p: r for (p, r) in punches}

            for (s_start, s_end) in shifts:
                # consider punches inside shift ± window
                start_win = s_start - timedelta(minutes=NO_PUNCH_WINDOW)
                end_win   = s_end   + timedelta(minutes=NO_PUNCH_WINDOW)
                near = [p for p in times_only if start_win <= p <= end_win]
                near.sort()

                if len(near) >= 2:
                    check_in, check_out = near[0], near[-1]
                elif len(near) == 1:
                    only = near[0]
                    if abs((only - s_start).total_seconds()) <= abs((only - s_end).total_seconds()):
                        check_in = only
                        check_out = s_end - timedelta(hours=AUTOCHECKOUT_HRS)
                    else:
                        check_in = s_start + timedelta(hours=AUTOCHECKOUT_HRS)
                        check_out = only
                else:
                    # no punch around this shift -> skip (treat as absence)
                    continue

                if check_out < check_in:
                    check_out = check_in + timedelta(minutes=1)

                # prevent duplicates in this shift
                existing = hr_att.search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', s_start),
                    ('check_in', '<=', s_end),
                ], limit=1)
                if existing:
                    # still mark used near punches as processed
                    for p in near:
                        punch_map[p].processed = True
                    continue

                # create hr.attendance (UTC naive already)
                hr_att.create({
                    'employee_id': employee.id,
                    'check_in':  check_in,
                    'check_out': check_out,
                })

                # mark used zk punches as processed
                for p in near:
                    punch_map[p].processed = True
