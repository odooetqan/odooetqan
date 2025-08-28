# -*- coding: utf-8 -*-
import logging
import xmlrpc.client
from datetime import datetime, timedelta, timezone

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def map_attendance_type(punch_type):
    # same mapping as the user's script
    mapping = {
        '0': '1',    # Check In  -> Finger
        '1': '1',    # Check Out -> Finger
        '2': '4',    # Break Out -> Card
        '3': '4',    # Break In  -> Card
        '4': '15',   # Overtime In  -> Face
        '5': '15',   # Overtime Out -> Face
        '255': '255' # Duplicate
    }
    return mapping.get(str(punch_type), '1')

class ZKAttendancePushJob(models.Model):
    _name = "zk.attendance.push.job"
    _description = "ZK Attendance Push Job"
    _order = "create_date desc"

    name = fields.Char(default=lambda self: fields.Datetime.now().strftime("Push %Y-%m-%d %H:%M:%S"))
    state = fields.Selection([("draft","Draft"),("running","Running"),("done","Done"),("failed","Failed")], default="draft")
    days_back = fields.Integer(string="Days Back", default=lambda self: self._get_default_days())
    last_run = fields.Datetime(readonly=True)
    log = fields.Text(readonly=True)
    created_count = fields.Integer(readonly=True)
    skipped_no_employee = fields.Integer(readonly=True)
    skipped_duplicates = fields.Integer(readonly=True)
    errors_count = fields.Integer(readonly=True)

    def _get_default_days(self):
        ICP = self.env["ir.config_parameter"].sudo()
        return int(ICP.get_param("zk_attendance_push_sh.days_back_default", "2") or 2)

    def _append_log(self, msg):
        ts = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for rec in self:
            rec.log = (rec.log or "") + f"[{ts}] {msg}\n"

    @api.model
    def cron_push(self):
        self.create({}).with_context(from_cron=True).action_run()

    def action_run(self):
        self.ensure_one()
        if self.state == "running":
            raise UserError(_("A push is already running."))
        self.write({"state":"running"})
        self._append_log("Starting ZK attendance push...")

        ICP = self.env["ir.config_parameter"].sudo()
        local_url = ICP.get_param("zk_attendance_push_sh.local_url") or ""
        local_db = ICP.get_param("zk_attendance_push_sh.local_db") or ""
        local_user = ICP.get_param("zk_attendance_push_sh.local_user") or ""
        local_password = ICP.get_param("zk_attendance_push_sh.local_password") or ""

        sh_url = ICP.get_param("zk_attendance_push_sh.sh_url") or ""
        sh_db = ICP.get_param("zk_attendance_push_sh.sh_db") or ""
        sh_user = ICP.get_param("zk_attendance_push_sh.sh_user") or ""
        sh_password = ICP.get_param("zk_attendance_push_sh.sh_password") or ""

        if not all([local_url, local_db, local_user, local_password, sh_url, sh_db, sh_user, sh_password]):
            self._append_log("Missing configuration parameters. Please fill Settings > Technical > System Parameters (via the provided settings panel).")
            self.write({"state": "failed"})
            raise UserError(_("Missing configuration parameters."))

        # Compute window
        try:
            days_back = int(self.days_back or self._get_default_days())
            if days_back <= 0:
                days_back = self._get_default_days()
        except Exception:
            days_back = self._get_default_days()

        now_utc = datetime.now(timezone.utc)
        date_from = now_utc - timedelta(days=days_back)
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        self._append_log(f"Fetching last {days_back} day(s), from {date_from_str}.")

        created = 0
        skipped_no_employee = 0
        skipped_duplicates = 0
        errors = 0

        try:
            # Authenticate to local
            common_local = xmlrpc.client.ServerProxy(f"{local_url}/xmlrpc/2/common", allow_none=True)
            uid_local = common_local.authenticate(local_db, local_user, local_password, {})
            if not uid_local:
                raise UserError(_("Failed to authenticate to local Odoo."))
            models_local = xmlrpc.client.ServerProxy(f"{local_url}/xmlrpc/2/object", allow_none=True)

            # Read local attendance in batches
            domain = [['punching_time', '>=', date_from_str]]
            fields_list = ['id', 'employee_id', 'punching_time', 'device_id_num', 'attendance_type', 'punch_type', 'address_id']
            limit = 2000
            offset = 0
            total = 0
            self._append_log("Reading local attendance in batches...")

            all_att = []
            while True:
                batch = models_local.execute_kw(local_db, uid_local, local_password,
                                               'zk.machine.attendance', 'search_read',
                                               [domain],
                                               {'fields': fields_list, 'limit': limit, 'offset': offset, 'order': 'punching_time asc'})
                if not batch:
                    break
                all_att.extend(batch)
                offset += limit
                total = len(all_att)
                self._append_log(f"... fetched {total} so far")

            self._append_log(f"Total fetched from local: {total}")

            # Authenticate to Odoo.sh
            common_sh = xmlrpc.client.ServerProxy(f"{sh_url}/xmlrpc/2/common", allow_none=True)
            uid_sh = common_sh.authenticate(sh_db, sh_user, sh_password, {})
            if not uid_sh:
                raise UserError(_("Failed to authenticate to Odoo.sh."))
            models_sh = xmlrpc.client.ServerProxy(f"{sh_url}/xmlrpc/2/object", allow_none=True)

            # Optional fields_get for sanity
            try:
                sh_fields = models_sh.execute_kw(sh_db, uid_sh, sh_password,
                                                 'zk.machine.attendance', 'fields_get', [], {'attributes': ['type']})
                self._append_log(f"Odoo.sh 'attendance_type' field meta: {sh_fields.get('attendance_type')}")
            except Exception as e:
                self._append_log(f"Could not fields_get on Odoo.sh: {e}")

            # Push
            for a in all_att:
                try:
                    device_id_num = a.get('device_id_num')
                    punching_time = a.get('punching_time')
                    punch_type = a.get('punch_type')

                    addr = a.get('address_id')
                    address_id = addr[0] if isinstance(addr, list) else addr

                    # find employee on Odoo.sh by device_id_num
                    emp = models_sh.execute_kw(sh_db, uid_sh, sh_password,
                                               'hr.employee', 'search_read',
                                               [[('device_id_num', '=', device_id_num)]],
                                               {'fields': ['id'], 'limit': 1})
                    if not emp:
                        skipped_no_employee += 1
                        continue
                    employee_id = emp[0]['id']

                    attendance_type = map_attendance_type(punch_type)

                    # dedup check
                    existing = models_sh.execute_kw(sh_db, uid_sh, sh_password,
                                                    'zk.machine.attendance', 'search',
                                                    [[
                                                        ('employee_id', '=', employee_id),
                                                        ('device_id_num', '=', device_id_num),
                                                        ('punching_time', '=', punching_time),
                                                        ('punch_type', '=', punch_type),
                                                    ]],
                                                    {'limit': 1})
                    if existing:
                        skipped_duplicates += 1
                        continue

                    models_sh.execute_kw(sh_db, uid_sh, sh_password,
                                         'zk.machine.attendance', 'create',
                                         [{
                                             'employee_id': employee_id,
                                             'punching_time': punching_time,
                                             'device_id_num': device_id_num,
                                             'punch_type': punch_type,
                                             'attendance_type': attendance_type,
                                             'address_id': address_id,
                                         }])
                    created += 1
                except Exception as e:
                    errors += 1
                    _logger.exception("Error pushing record: %s", e)

            self.write({
                "state": "done",
                "last_run": fields.Datetime.now(),
                "created_count": created,
                "skipped_no_employee": skipped_no_employee,
                "skipped_duplicates": skipped_duplicates,
                "errors_count": errors,
            })
            self._append_log(f"SUMMARY: created={created}, skipped_no_employee={skipped_no_employee}, skipped_duplicates={skipped_duplicates}, errors={errors}")
        except Exception as e:
            self._append_log(f"ERROR: {e}")
            _logger.exception("ZK push failed: %s", e)
            self.write({"state":"failed"})
            raise
