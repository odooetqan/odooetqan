# -*- coding: utf-8 -*-
import logging
import json
import requests
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from psycopg2 import IntegrityError, Error as PsycoError
import base64

_logger = logging.getLogger(__name__)

# --------------------------
# URL helpers
# --------------------------
def _normalize_origin(u: str) -> str:
    """Return scheme://host[:port] with no path/query/fragment."""
    u = (u or "").strip()
    sp = urlsplit(u)
    if not sp.scheme or not sp.netloc:
        raise UserError(_("Invalid API Base URL: %s") % (u or "<empty>"))
    return urlunsplit((sp.scheme, sp.netloc, "", "", ""))


def _api_url(origin: str, path: str) -> str:
    """Join origin + /api + path safely (path may start with /)."""
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    return f"{origin}/api{p}"


class BiostarDevice(models.Model):
    _name = "biostar.device"
    _description = "Suprema BioStar Device"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # --------------------------
    # Fields
    # --------------------------
    name = fields.Char(required=True, tracking=True)
    base_url = fields.Char(
        "API Base URL", required=True,
        help="Origin only (no /api). Example: https://10.201.2.88:5002"
    )
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    verify_ssl = fields.Boolean(default=False)
    device_ip = fields.Char("Device IP")
    timezone = fields.Char(default="UTC")
    token = fields.Char("Session Token", readonly=True)
    token_expires = fields.Datetime(readonly=True)

    active = fields.Boolean(default=True)
    last_user_sync = fields.Datetime(readonly=True)
    last_event_sync = fields.Datetime(readonly=True)
    status = fields.Selection(
        [('unknown', 'Unknown'), ('ok', 'OK'), ('error', 'Error')],
        default='unknown', readonly=True
    )
    status_message = fields.Char(readonly=True)

    user_ids = fields.One2many('biostar.user', 'device_id', string="Users")


    # Student timing knobs (used by Student Attendance processor)
    start_attendance_student = fields.Float(
        string="Student Start Hour",
        help="School start time as a float hour, e.g., 8.0 means 08:00.",
        default=8.0,
    )
    time_to_present_late = fields.Integer(
        string="Late After (min)",
        help="Minutes after start to still be counted Present; beyond that -> Late.",
        default=10,
    )
    time_to_calculate_absent = fields.Integer(
        string="Absent After (min)",
        help="Minutes after start to mark as Absent if no check-in.",
        default=60,
    )

    # processing knobs (employees)
    min_gap_seconds = fields.Integer(default=60, help="Ignore repeated punches within this gap.")
    max_shift_hours = fields.Integer(default=16, help="Auto close a shift longer than this.")
    prefer_first_in = fields.Boolean(default=True, help="If direction unknown, alternate starting with IN.")

    # Operating mode (so you can skip employee processor on student-only devices)
    attendance_mode = fields.Selection(
        [('employee', 'Employee'), ('student', 'Student')],
        string="Attendance Mode", default='employee'
    )


    # in biostar.device fields section
    default_user_group_id = fields.Integer(
        string="Default User Group ID",
        help="If set, force this User Group when creating users on BioStar."
    )
    default_partition_id = fields.Integer(
        string="Default Partition/Site ID",
        help="If set, force this Partition/Site when creating users on BioStar."
    )



    # --------------------------
    # Internals / utilities
    # --------------------------
    def _safe_write(self, rec, vals):
        """Bypass any accidental shadowing of instance .write."""
        return type(rec).write(rec, vals)

    def _session(self):
        s = requests.Session()
        s.verify = bool(self.verify_ssl)
        origin = _normalize_origin(self.base_url)
        s.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Odoo-BioStar/1.0",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": origin,
            "Referer": origin + "/",
        })
        return s

    def _login(self):
        """Login and return a record with fresh cookies/session in its context."""
        for rec in self:
            origin = _normalize_origin(rec.base_url)
            url = _api_url(origin, "/login")
            payload = {"User": {"login_id": rec.username, "password": rec.password}}

            s = rec._session()
            r = s.post(url, json=payload, timeout=30, allow_redirects=False)

            bs_sid = r.headers.get("bs-session-id")
            ok = (r.status_code == 200) or bool(bs_sid)
            if not ok:
                raise UserError(_("Login failed (%s): %s") % (r.status_code, r.text or r.reason))

            cookies = s.cookies.get_dict()
            if bs_sid:
                cookies["bs-session-id"] = bs_sid

            self._safe_write(rec, {
                "token": "COOKIE",
                "token_expires": fields.Datetime.now() + timedelta(hours=1),
            })

            return rec.with_context(_cookies=cookies, _bs_sid=bs_sid or "")
        return self

    # def _req(self, method, path, **kw):
    #     """Do a request under /api/<path>. Retry once on 401/419 by re-login."""
    #     self.ensure_one()
    #     origin = _normalize_origin(self.base_url)
    #     url = _api_url(origin, path)

    #     s = self._session()

    #     # restore session
    #     cookies = dict(self.env.context.get('_cookies') or {})
    #     if cookies:
    #         s.cookies.update(cookies)
    #     bs_sid = self.env.context.get('_bs_sid')
    #     if bs_sid:
    #         s.headers["bs-session-id"] = bs_sid

    #     r = s.request(method.upper(), url, timeout=60, **kw)

    #     if r.status_code in (401, 419):  # expired/missing session
    #         recc = self._login()
    #         s = recc._session()
    #         cookies = dict(recc.env.context.get('_cookies') or {})
    #         if cookies:
    #             s.cookies.update(cookies)
    #         bs_sid = recc.env.context.get('_bs_sid')
    #         if bs_sid:
    #             s.headers["bs-session-id"] = bs_sid
    #         r = s.request(method.upper(), url, timeout=60, **kw)

    #     r.raise_for_status()
    #     if not r.text:
    #         return {}
    #     try:
    #         return r.json()
    #     except Exception:
    #         return {"_raw": r.text}

    def _req(self, method, path, **kw):
        """Do a request under /api/<path>. Retry once on 401/419 by re-login."""
        self.ensure_one()
        origin = _normalize_origin(self.base_url)
        url = _api_url(origin, path)

        s = self._session()

        # restore session
        cookies = dict(self.env.context.get('_cookies') or {})
        if cookies:
            s.cookies.update(cookies)
        bs_sid = self.env.context.get('_bs_sid')
        if bs_sid:
            s.headers["bs-session-id"] = bs_sid

        r = s.request(method.upper(), url, timeout=60, **kw)

        if r.status_code in (401, 419):  # expired/missing session
            recc = self._login()
            s = recc._session()
            cookies = dict(recc.env.context.get('_cookies') or {})
            if cookies:
                s.cookies.update(cookies)
            bs_sid = recc.env.context.get('_bs_sid')
            if bs_sid:
                s.headers["bs-session-id"] = bs_sid
            r = s.request(method.upper(), url, timeout=60, **kw)

        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            # show BioStar body in Odoo error
            raise UserError(f"BioStar API {r.status_code} on {path}:\n{r.text}") from e

        if not r.text:
            return {}
        try:
            return r.json()
        except Exception:
            return {"_raw": r.text}

    # add near _req()
    def _req_raw(self, method, path, **kw):
        """Same as _req but returns the raw requests.Response (for image bytes)."""
        self.ensure_one()
        origin = _normalize_origin(self.base_url)
        url = _api_url(origin, path)

        s = self._session()
        cookies = dict(self.env.context.get('_cookies') or {})
        if cookies:
            s.cookies.update(cookies)
        bs_sid = self.env.context.get('_bs_sid')
        if bs_sid:
            s.headers["bs-session-id"] = bs_sid

        r = s.request(method.upper(), url, timeout=60, **kw)
        if r.status_code in (401, 419):
            recc = self._login()
            s = recc._session()
            cookies = dict(recc.env.context.get('_cookies') or {})
            if cookies:
                s.cookies.update(cookies)
            bs_sid = recc.env.context.get('_bs_sid')
            if bs_sid:
                s.headers["bs-session-id"] = bs_sid
            r = s.request(method.upper(), url, timeout=60, **kw)

        # don't raise here; caller may want to inspect content-type
        return r

    def _get_internal_user_id(self, recc, user_code):
        """Return BioStar internal numeric id for a given user code (string)."""
        try:
            body = {
                "Query": {
                    "limit": 1,
                    "offset": 0,
                    "conditions": [{
                        "column": "user_id.user_id",
                        "operator": 0,
                        "values": [str(user_code)]
                    }]
                }
            }
            data = recc._req("POST", "/users/search", json=body)
            row = (data or {}).get("UserCollection", {}).get("rows") or []
            if row and isinstance(row[0], dict) and row[0].get("id") is not None:
                return int(row[0]["id"])
        except Exception as e:
            _logger.info("Lookup internal id for %s failed: %s", user_code, e)
        return None


    def _fetch_biostar_user_image(self, recc, internal_id):
        """
        Return (bytes, mimetype) for user photo if available, else (None, None).
        Tries common v2 and v1 endpoints.
        """
        if internal_id is None:
            return None, None

        # most friendly first
        candidates = [
            ("GET", f"/v2/users/{internal_id}/photo"),          # v2
            ("GET", f"/users/{internal_id}/photo"),             # v1
            ("GET", f"/users/{internal_id}/profile_image"),     # v1 alt
            ("GET", f"/users/profile_image/{internal_id}"),     # v1 alt
            ("GET", f"/users/{internal_id}/image"),             # some firmwares
        ]

        for method, path in candidates:
            try:
                r = recc._req_raw(method, path, stream=False)
                if r.status_code == 200:
                    ctype = (r.headers.get("Content-Type") or "").lower()
                    if ctype.startswith("image/") and r.content:
                        return r.content, ctype
                    # some servers send octet-stream but it’s still an image
                    if r.content and len(r.content) > 1000 and "image" in r.headers.get("Content-Disposition","").lower():
                        return r.content, ctype or "application/octet-stream"
                elif r.status_code in (404, 400):
                    continue
            except Exception as e:
                _logger.info("Photo fetch failed @ %s: %s", path, e)
                continue
        return None, None



    def action_pull_user_images(self):
        """
        For each biostar.user linked to this device (and mapped to student/employee),
        fetch photo from BioStar and set on res.partner.image_1920 and hr.employee.image_1920.
        """
        BiostarUser = self.env['biostar.user'].sudo()

        for rec in self:
            recc = rec._login()
            users = BiostarUser.search([('device_id', '=', rec.id)])
            got, set_emp, set_stu = 0, 0, 0

            for bu in users:
                uid = (bu.biostar_user_id or "").strip()
                if not uid:
                    continue

                iid = rec._get_internal_user_id(recc, uid)
                img, mt = rec._fetch_biostar_user_image(recc, iid)
                if not img:
                    continue

                # b64 = base64.b64encode(img)
                b64 = base64.b64encode(img).decode()  # str
                got += 1

                # student partner
                if getattr(bu, 'student_id', False) and bu.student_id:
                    try:
                        bu.student_id.sudo().write({'image_1920': b64})
                        set_stu += 1
                    except Exception as e:
                        _logger.info("Set student image failed (%s): %s", uid, e)

                # employee + employee's private address partner
                if bu.employee_id:
                    try:
                        bu.employee_id.sudo().write({'image_1920': b64})
                        set_emp += 1
                    except Exception as e:
                        _logger.info("Set employee image failed (%s): %s", uid, e)
                    # write also on related partner if exists
                    partner = bu.employee_id.sudo().address_home_id
                    if partner:
                        try:
                            partner.write({'image_1920': b64})
                        except Exception:
                            pass

            # toast
            try:
                self.env['bus.bus']._sendone(
                    self.env.user.partner_id, 'simple_notification',
                    {'title': _('BioStar'),
                    'message': _("User photos: downloaded %s; set on %s employees, %s students.") % (got, set_emp, set_stu),
                    'sticky': False}
                )
            except Exception:
                pass

        return True



    # --------------------------
    # Parsing helpers
    # --------------------------
    def _extract_users(self, payload):
        """Return a flat list of user dicts or strings from any BioStar response."""
        if payload is None:
            return []

        # String? try JSON, else split lines
        if isinstance(payload, str):
            s = payload.strip()
            if s and s[0] in "[{]":
                try:
                    payload = json.loads(s)
                except Exception:
                    return [line.strip() for line in s.splitlines() if line.strip()]
            else:
                return [line.strip() for line in s.splitlines() if line.strip()]

        # Envelope with Response?
        if isinstance(payload, dict) and isinstance(payload.get("Response"), dict):
            code = payload["Response"].get("code")
            if code is not None and str(code) != "0":
                _logger.warning("BioStar Response error: %s", payload["Response"])
                return []

        # Exact BioStar shape: {"UserCollection":{"rows":[...]} }
        if isinstance(payload, dict):
            uc = payload.get("UserCollection")
            if isinstance(uc, dict) and isinstance(uc.get("rows"), list) and uc["rows"]:
                return uc["rows"]

        out = []

        def looks_like_user(d):
            if not isinstance(d, dict):
                return False
            keys = {k.lower() for k in d.keys()}
            return bool(keys & {"user_id", "id", "userid", "usercode", "user_code"}) or \
                   ("name" in keys or "username" in keys or "display_name" in keys)

        def walk(x):
            if x is None:
                return
            if isinstance(x, dict):
                if looks_like_user(x):
                    out.append(x)
                for k, v in x.items():
                    if k in ("records", "data", "users", "UserList", "UserCollection", "Items", "results", "items", "rows"):
                        walk(v)
                    else:
                        walk(v)
            elif isinstance(x, list):
                for i in x:
                    walk(i)
            elif isinstance(x, str):
                s = x.strip()
                if s:
                    out.append(s)

        walk(payload)
        return out

    def _parse_biostar_dt(self, ts):
        """Normalize BioStar ISO strings like 2025-09-15T14:07:16.00Z to Odoo datetime."""
        if not ts:
            return False
        s = str(ts).strip()
        s = s.replace("T", " ")
        if s.endswith("Z"):
            s = s[:-1]
        if "." in s:
            s = s.split(".")[0]
        return fields.Datetime.from_string(s)

    # --------------------------
    # Buttons / public API
    # --------------------------
    def action_test_connection(self):
        for rec in self:
            try:
                recc = rec._login()
                try:
                    _ = recc._req("POST", "/devices/search", json={"Query": {}, "Limit": 1})
                except Exception:
                    _ = recc._req("GET", "/system")
                rec.write({"status": "ok", "status_message": "Connected Success"})
            except Exception as e:
                _logger.exception("BioStar test failed")
                self._safe_write(rec, {"status": "error", "status_message": str(e)})
                raise
        return True

    def action_import_users(self):
        """Create/update biostar.user records from BioStar, and auto-link to employee/student."""
        BiostarUser = self.env['biostar.user'].sudo()

        for rec in self:
            recc = rec._login()

            items = []
            raw_samples = []

            # 1) Try POST /api/users/search with pagination
            try:
                limit, offset, loops = 200, 0, 0
                while True:
                    body = {"Query": {}, "Limit": limit, "Offset": offset}
                    data = recc._req("POST", "/users/search", json=body)
                    if len(raw_samples) < 2:
                        raw_samples.append(str(data)[:600])
                    chunk = recc._extract_users(data)
                    if not chunk:
                        break
                    items.extend(chunk)
                    if len(chunk) < limit:
                        break
                    offset += limit
                    loops += 1
                    if loops > 50:
                        break
            except Exception as e:
                _logger.info("POST /api/users/search failed: %s", e)

            # 2) Fallback GET /api/users
            if not items:
                try:
                    limit, offset, loops = 200, 0, 0
                    while True:
                        data = recc._req("GET", f"/users?limit={limit}&offset={offset}")
                        if len(raw_samples) < 2:
                            raw_samples.append(str(data)[:600])
                        chunk = recc._extract_users(data)
                        if not chunk:
                            break
                        items.extend(chunk)
                        if len(chunk) < limit:
                            break
                        offset += limit
                        loops += 1
                        if loops > 50:
                            break
                except Exception as e:
                    _logger.info("GET /api/users fallback failed: %s", e)

            # Optional probe (diagnostic)
            if not items:
                try:
                    _ = recc._req("POST", "/devices/search", json={"Query": {}, "Limit": 1})
                except Exception as e:
                    _logger.info("POST /api/devices/search probe failed: %s", e)

            if not items:
                _logger.warning("No users extracted. Samples: %s", " | ".join(raw_samples) or "<empty>")
                try:
                    self.env['bus.bus']._sendone(
                        self.env.user.partner_id, 'simple_notification',
                        {'title': _('BioStar'),
                         'message': _("User import: no users returned (check API user permissions/endpoint)."),
                         'sticky': False}
                    )
                except Exception:
                    pass
                continue

            created, updated = 0, 0
            now = fields.Datetime.now()

            # Prefetch employees/students to avoid N x search()
            # (Safe if you expect large imports; otherwise skip for simplicity)
            try:
                uids = []
                for u in items:
                    if isinstance(u, str):
                        uids.append(u.strip())
                    else:
                        uid = str(u.get("user_id") or u.get("id") or u.get("user_code") or
                                  u.get("userID") or u.get("UserID") or u.get("code") or "").strip()
                        if uid:
                            uids.append(uid)
                uids = list({x for x in uids if x})
                emp_map = {e.barcode: e for e in self.env['hr.employee'].sudo().search([('barcode', 'in', uids)])}
                stu_map = {p.student_number: p for p in self.env['res.partner'].sudo().search([('student_number', 'in', uids)])}
            except Exception:
                emp_map, stu_map = {}, {}

            for u in items:
                if isinstance(u, str):
                    uid = u.strip()
                    name = uid
                    card = None
                else:
                    uid = str(
                        u.get("user_id") or u.get("id") or u.get("user_code") or
                        u.get("userID") or u.get("UserID") or u.get("code") or ""
                    ).strip()
                    name = (u.get("name") or u.get("display_name") or u.get("UserName") or uid or "").strip()
                    card = u.get("card") or u.get("card_no") or u.get("CardNo") or u.get("rfid")
                    if card is not None:
                        card = str(card).strip()

                if not uid:
                    continue

                rec_user = BiostarUser.search([
                    ('device_id', '=', rec.id),
                    ('biostar_user_id', '=', uid)
                ], limit=1)

                vals = {"name": name or uid}
                if card:
                    vals["card_no"] = card

                try:
                    with self.env.cr.savepoint():
                        if rec_user:
                            type(rec_user).write(rec_user, vals)
                            updated += 1
                        else:
                            vals.update({"device_id": rec.id, "biostar_user_id": uid})
                            rec_user = BiostarUser.create(vals)
                            created += 1

                        # --- Auto-link per user (employee first, else student) ---
                        emp = emp_map.get(uid) or self.env['hr.employee'].sudo().search([('barcode', '=', uid)], limit=1)
                        if emp and not rec_user.employee_id:
                            rec_user.employee_id = emp.id
                        if not emp and not getattr(rec_user, 'student_id', False):
                            stu = stu_map.get(uid) or self.env['res.partner'].sudo().search([('student_number', '=', uid)], limit=1)
                            if stu:
                                rec_user.student_id = stu.id
                except Exception as ex:
                    _logger.exception("Skipping user sync row (%s): %s", uid, ex)
                    self.env.cr.rollback()
                    continue

            self._safe_write(rec, {'last_user_sync': now})
            try:
                self.env['bus.bus']._sendone(
                    self.env.user.partner_id, 'simple_notification',
                    {'title': _('BioStar'),
                     'message': _("User import finished. Created: %s, Updated: %s") % (created, updated),
                     'sticky': False}
                )
            except Exception:
                pass
        return True

    # --------------------------
    # Helpers for student processing
    # --------------------------
    def _device_local_date(self, rec, dt_utc):
        """Return date of dt_utc in device timezone (fallback to UTC)."""
        local_dt = fields.Datetime.context_timestamp(rec.with_context(tz=rec.timezone or 'UTC'), dt_utc)
        return fields.Date.to_date(local_dt)

    def _process_student_logs(self):
        """Build/Update student.attendance from raw logs."""
        Log = self.env['biostar.attendance.log'].sudo()
        Att = self.env['student.attendance'].sudo()
        BiostarUser = self.env['biostar.user'].sudo()
        Partner = self.env['res.partner'].sudo()

        for rec in self:
            try:
                domain = [('device_id', '=', rec.id), ('state', '=', 'draft')]
                logs = Log.search(domain, order="event_dt_utc")
            except Exception:
                self.env.cr.rollback()
                logs = Log.search([('device_id', '=', rec.id), ('state', '=', 'draft')], order="event_dt_utc")

            if not logs:
                continue

            # group by (student_id, local_date)
            buckets = {}  # key: (sid, date) -> [logs]
            for lg in logs:
                uid = (lg.biostar_user_id or "").strip()
                if not uid:
                    continue

                stu = False
                try:
                    # 1) via biostar.user link (preferred)
                    bu = BiostarUser.search([
                        ('device_id', '=', rec.id),
                        ('biostar_user_id', '=', uid),
                        ('student_id', '!=', False)
                    ], limit=1)
                    stu = bu.student_id if bu else False

                    # 2) fallback by student_number == uid
                    if not stu:
                        stu = Partner.search([('student_number', '=', uid)], limit=1)
                except Exception:
                    self.env.cr.rollback()
                    continue

                if not stu:
                    # leave it draft so it can still feed employee flow if mapped there
                    continue

                day = self._device_local_date(rec, lg.event_dt_utc)
                buckets.setdefault((stu.id, day), []).append(lg)

            # create/update attendance per (student, day)
            for (sid, day), items in buckets.items():
                try:
                    with self.env.cr.savepoint():
                        first_dt = min(i.event_dt_utc for i in items if i.event_dt_utc)
                        vals = {
                            'first_check_in': first_dt,
                            'device_id': rec.id,
                        }
                        state = Att._student_status_from_checkin(rec, day, first_dt)
                        vals['state'] = state

                        att = Att.search([('student_id', '=', sid), ('attendance_date', '=', day)], limit=1)
                        if att:
                            att.write(vals)
                        else:
                            Att.create({
                                'student_id': sid,
                                'attendance_date': day,
                                **vals,
                            })

                        # mark those logs processed (student path)
                        for lg in items:
                            lg.write({'state': 'processed', 'note': 'student'})
                except Exception as ex:
                    _logger.exception("Student processor skipped (student %s, day %s): %s", sid, day, ex)
                    self.env.cr.rollback()
                    continue

    # --------------------------
    # Event pulling
    # --------------------------
    def action_pull_events(self, since=None, until=None, user_filter=None, device_filter=None):
        """
        Fetch BioStar events (EventCollection.rows) -> biostar.attendance.log, then process.
        Hardened so one bad row can't abort the whole request.
        """
        Log = self.env["biostar.attendance.log"].sudo()
        Employee = self.env["hr.employee"].sudo()
        BiostarUser = self.env["biostar.user"].sudo()

        def _rows(payload):
            if isinstance(payload, dict):
                ec = payload.get("EventCollection") or {}
                rows = ec.get("rows") or []
                if isinstance(rows, list):
                    return rows
            return []

        CODE_IN  = {"4867"}  # map success codes to IN as needed
        CODE_OUT = set()

        for rec in self:
            recc = rec._login()

            # default window = last 365d
            since_dt = fields.Datetime.from_string(since) if since else (fields.Datetime.now() - timedelta(days=365))
            until_dt = fields.Datetime.from_string(until) if until else fields.Datetime.now()

            conditions = [{
                "column": "datetime",
                "operator": 3,  # BETWEEN
                "values": [
                    since_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    until_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                ],
            }]
            if user_filter:
                conditions.append({"column": "user_id.user_id", "operator": 0, "values": [str(user_filter)]})
            if device_filter:
                conditions.append({"column": "device_id.id", "operator": 0, "values": [str(device_filter)]})

            limit = 500
            offset = 0
            created = 0

            while True:
                body = {
                    "Query": {
                        "limit": limit,
                        "offset": offset,
                        "conditions": conditions,
                        "orders": [{"column": "datetime", "descending": False}],
                    }
                }
                data = recc._req("POST", "/events/search", json=body)
                rows = _rows(data)
                if not rows:
                    break

                for ev in rows:
                    try:
                        with self.env.cr.savepoint():
                            ev_id = str(ev.get("id") or "").strip()

                            ts = ev.get("server_datetime") or ev.get("datetime")
                            dt_utc = self._parse_biostar_dt(ts)
                            if not dt_utc:
                                continue

                            uid = ""
                            u = ev.get("user_id") or {}
                            if isinstance(u, dict):
                                uid = str(u.get("user_id") or "").strip()
                            if not uid:
                                uid = str(ev.get("user_id") or ev.get("user_code") or "").strip()
                            if not uid:
                                continue

                            code = str((ev.get("event_type_id") or {}).get("code") or "").strip()
                            direction = "in" if code in CODE_IN else ("out" if code in CODE_OUT else None)

                            external_key = f"{rec.id}:{ev_id}" if ev_id else f"{rec.id}:{uid}:{dt_utc.isoformat()}"

                            emp = Employee.search([("barcode", "=", uid)], limit=1)
                            if not emp:
                                bs_user = BiostarUser.search(
                                    [("device_id", "=", rec.id), ("biostar_user_id", "=", uid), ("employee_id", "!=", False)],
                                    limit=1
                                )
                                emp = bs_user.employee_id

                            vals = {
                                "device_id": rec.id,
                                "employee_id": emp.id if emp else False,
                                "biostar_user_id": uid,
                                "event_dt_utc": dt_utc,
                                "event_time": dt_utc,
                                "event_type": code,
                                "external_key": external_key,
                                "state": "draft",
                            }
                            if direction in ("in", "out"):
                                vals["direction"] = direction

                            Log.create(vals)
                            created += 1
                    except IntegrityError as ex:
                        _logger.info("Skip duplicate/constraint for device %s: %s", rec.id, ex)
                        self.env.cr.rollback()
                        continue
                    except PsycoError as ex:
                        _logger.info("PostgreSQL error on device %s: %s", rec.id, ex)
                        self.env.cr.rollback()
                        continue
                    except Exception as ex:
                        _logger.exception("Failed to import BioStar event on device %s", rec.id)
                        self.env.cr.rollback()
                        continue

                if len(rows) < limit:
                    break
                offset += limit

            # watermark
            self._safe_write(rec, {"last_event_sync": fields.Datetime.now()})

            # process inside savepoints; never poison the request
            try:
                with self.env.cr.savepoint():
                    self._process_logs()
            except Exception:
                _logger.exception("Processing logs failed; skipped for device %s", rec.id)
                self.env.cr.rollback()
            try:
                with self.env.cr.savepoint():
                    self._process_student_logs()
            except Exception:
                _logger.exception("Processing student logs failed; skipped for device %s", rec.id)
                self.env.cr.rollback()

            try:
                self.env["bus.bus"]._sendone(
                    self.env.user.partner_id, "simple_notification",
                    {"title": _("BioStar"),
                     "message": _("Pulled %s new raw events; processed to attendances.") % created,
                     "sticky": False}
                )
            except Exception:
                pass

        return True

    def action_pull_events_24(self, since=None, until=None, user_filter=None, device_filter=None):
        """Same as action_pull_events but default window is last 24h."""
        since = since or (fields.Datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        until = until or fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.action_pull_events(since=since, until=until,
                                       user_filter=user_filter, device_filter=device_filter)

    # --------------------------
    # Employee attendance processor
    # --------------------------
    def _process_logs(self):
        """Convert unprocessed biostar.attendance.log to hr.attendance with simple policies."""
        Log = self.env['biostar.attendance.log'].sudo()
        Attendance = self.env['hr.attendance'].sudo()

        for rec in self:
            # Skip if this particular device is Student-only
            if rec.attendance_mode == 'student':
                continue

            # Be defensive: if we came here with a dirty txn, clean then retry once
            try:
                domain = [('device_id', '=', rec.id), ('state', '=', 'draft')]
                logs = Log.search(domain, order="employee_id, event_dt_utc")
            except Exception:
                self.env.cr.rollback()
                logs = Log.search([('device_id', '=', rec.id), ('state', '=', 'draft')],
                                  order="employee_id, event_dt_utc")

            if not logs:
                continue

            min_gap = timedelta(seconds=int(rec.min_gap_seconds or 60))
            max_shift = timedelta(hours=int(rec.max_shift_hours or 16))

            by_emp = {}
            for lg in logs:
                by_emp.setdefault(lg.employee_id.id or 0, []).append(lg)

            for emp_id, items in by_emp.items():
                if not emp_id:
                    # for lg in items:
                        # try:
                        #     # with self.env.cr.savepoint():
                        #         # lg.write({'state': 'skipped', 'note': 'No employee mapping'})
                        # except Exception:
                        #     self.env.cr.rollback()
                    continue

                items.sort(key=lambda r: (r.event_dt_utc, r.id))
                last_att = Attendance.search([('employee_id', '=', emp_id)], order='check_in desc', limit=1)

                expect = 'in' if self.prefer_first_in else 'out'
                if last_att and not last_att.check_out:
                    expect = 'out'

                prev_dt = None
                for lg in items:
                    try:
                        with self.env.cr.savepoint():
                            if prev_dt and (lg.event_dt_utc - prev_dt) < min_gap:
                                lg.write({'state': 'skipped', 'note': 'Within min_gap'})
                                prev_dt = lg.event_dt_utc
                                continue

                            eff_dir = getattr(lg, 'direction', False) or False
                            if not eff_dir:
                                eff_dir = expect
                                expect = 'out' if eff_dir == 'in' else 'in'

                            if not last_att or last_att.check_out:
                                if eff_dir == 'out':
                                    lg.write({'state': 'skipped', 'note': 'Unexpected OUT'})
                                    prev_dt = lg.event_dt_utc
                                    continue
                                last_att = Attendance.create({
                                    'employee_id': emp_id,
                                    'check_in': lg.event_dt_utc,
                                })
                                lg.write({'state': 'processed', 'attendance_id': last_att.id})
                            else:
                                close_now = (eff_dir == 'out')
                                if not close_now and (lg.event_dt_utc - last_att.check_in) > max_shift:
                                    close_now = True

                                if close_now and lg.event_dt_utc > last_att.check_in:
                                    last_att.write({'check_out': lg.event_dt_utc})
                                    lg.write({'state': 'processed', 'attendance_id': last_att.id})
                                    last_att = Attendance.search([('employee_id', '=', emp_id)], order='check_in desc', limit=1)
                                else:
                                    lg.write({'state': 'skipped', 'note': 'Ignored (no close)'})

                            prev_dt = lg.event_dt_utc
                    except Exception as ex:
                        _logger.exception("Processor skipped a row (emp %s, log %s): %s", emp_id, lg.id, ex)
                        self.env.cr.rollback()
                        continue

    # (Legacy helpers kept for compatibility with your menus/buttons)
    def action_pull_logs(self, since=None, until=None):
        Log = self.env["biostar.attendance.log"].sudo()
        for rec in self:
            recc = rec._login()
            since_dt = fields.Datetime.from_string(since) if since else (fields.Datetime.now() - timedelta(days=1))
            until_dt = fields.Datetime.from_string(until) if until else fields.Datetime.now()

            body = {
                "Query": {
                    "limit": 500,
                    "conditions": [{
                        "column": "datetime",
                        "operator": 3,
                        "values": [
                            since_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                            until_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        ]
                    }],
                    "orders": [{"column": "datetime", "descending": False}],
                }
            }
            data = recc._req("POST", "/events/search", json=body)
            rows = (data or {}).get("EventCollection", {}).get("rows") or []
            for ev in rows:
                try:
                    with self.env.cr.savepoint():
                        uid = str(((ev.get("user_id") or {}).get("user_id") or ev.get("user_code") or "")).strip()
                        ts = ev.get("server_datetime") or ev.get("datetime")
                        if not uid or not ts:
                            continue
                        dt_utc = self._parse_biostar_dt(ts)
                        Log.create({
                            "device_id": rec.id,
                            "biostar_user_id": uid,
                            "employee_id": self.env["hr.employee"].search([("barcode", "=", uid)], limit=1).id or False,
                            "event_dt_utc": dt_utc,
                            "event_time": dt_utc,
                            "event_type": str((ev.get("event_type_id") or {}).get("code") or ""),
                            "state": "draft",
                        })
                except Exception:
                    self.env.cr.rollback()
                    continue

    def process_logs(self):
        """Very old helper; kept for compatibility."""
        Log = self.env["biostar.attendance.log"].sudo()
        Attendance = self.env["hr.attendance"].sudo()

        logs = Log.search([], order="event_time asc")
        for log in logs:
            try:
                with self.env.cr.savepoint():
                    if not log.employee_id:
                        # return
                        continue
                    last = Attendance.search([("employee_id", "=", log.employee_id.id)], order="check_in desc", limit=1)
                    if not last or last.check_out:
                        Attendance.create({"employee_id": log.employee_id.id, "check_in": log.event_time})
                    else:
                        if log.event_time > last.check_in:
                            last.write({"check_out": log.event_time})
            except Exception:
                self.env.cr.rollback()
                continue

    # --------------------------
    # BioStar User push helpers
    # --------------------------
    def _search_device_user(self, recc, uid):
        """Return first user row for uid from BioStar2, or None."""
        try:
            body = {
                "Query": {
                    "limit": 1,
                    "offset": 0,
                    "conditions": [{
                        "column": "user_id.user_id",  # match by 'user code' field
                        "operator": 0,                # EQUAL
                        "values": [str(uid)]
                    }]
                }
            }
            data = recc._req("POST", "/users/search", json=body)
            uc = (data or {}).get("UserCollection") or {}
            rows = uc.get("rows") or []
            return rows[0] if rows else None
        except Exception as e:
            _logger.info("BioStar search user %s failed: %s", uid, e)
            return None

    # --- add this helper near _search_device_user ---
    def _get_default_user_group(self, recc):
        """Return a {'id': <int>} dict for some valid user group, or None."""
        try:
            body = {"Query": {"limit": 1, "offset": 0}}
            data = recc._req("POST", "/user_groups/search", json=body)
            rows = (data or {}).get("UserGroupCollection", {}).get("rows") or []
            if rows and isinstance(rows[0], dict) and rows[0].get("id"):
                return {"id": rows[0]["id"]}
        except Exception as e:
            _logger.info("BioStar user_groups probe failed: %s", e)
        return None


    def _post_user_with_fallbacks(self, recc, candidate_bodies):
        """Try POST /users with several bodies; return JSON on first success or raise last error."""
        last_err = None
        for body in candidate_bodies:
            try:
                return recc._req("POST", "/users", json=body)
            except Exception as e:
                last_err = e
                # 4xx/5xx – try the next shape
                continue
        # Exhausted all bodies: raise with useful server text
        resp_text = getattr(getattr(last_err, 'response', None), 'text', '') or str(last_err)
        raise UserError(_("Failed to create user on BioStar: %s") % resp_text)


    # def _upsert_device_user(self, recc, uid, name=None, card_no=None):
    #     uid = str(uid or "").strip()
    #     if not uid:
    #         raise UserError(_("Student number (user code) is required."))

    #     existing = self._search_device_user(recc, uid)
    #     display_name = name or uid
    #     group_id, partition_id = self._pick_valid_user_group_id(recc)  # (int|None, int|None)

    #     def with_card(payload_user):
    #         if card_no:
    #             payload_user["card"] = {"card_id": str(card_no)}
    #         return payload_user

    #     # Base variants for the user identity
    #     existing = self._search_device_user(recc, uid)
    #     display_name = name or uid
    #     group_id, partition_id = self._pick_valid_user_group_id(recc)

    #     def with_card(p):
    #         if card_no:
    #             p["card"] = {"card_id": str(card_no)}
    #         return p

    #     # Identity variants
    #     base_variants = [
    #         {"user_id": {"user_id": uid}, "login_id": uid, "name": display_name},
    #         {"user_id": uid,              "login_id": uid, "name": display_name},
    #         {"user_id": {"user_id": uid},                 "name": display_name},
    #     ]
    #     if uid.isdigit():
    #         pin4 = uid[-4:].rjust(4, "0")
    #         base_variants.append({"user_id": uid, "login_id": uid, "name": display_name, "pin": pin4})

    #     # Group shapes
    #     group_shapes = [{}]
    #     if group_id is not None:
    #         gid = int(group_id)
    #         group_shapes = [
    #             {"user_group_id": gid},
    #             {"user_group_id": {"id": gid}},
    #             {"user_group":    {"id": gid}},
    #             {"user_groups":   [{"id": gid}]},
    #             {"user_group_ids":[{"id": gid}]},
    #         ]

    #     # Partition/Site shapes
    #     part_shapes = [{}]
    #     if partition_id is not None:
    #         pid = int(partition_id)
    #         part_shapes = [
    #             {"partition_id": pid},
    #             {"partition":    {"id": pid}},
    #             {"site_id":      pid},          # some builds call it site/site_id
    #             {"site":         {"id": pid}},
    #         ]

    #     create_candidates = []
    #     for base in base_variants:
    #         # full cross product
    #         for g in group_shapes:
    #             for p in part_shapes:
    #                 create_candidates.append({"User": with_card({**base, **g, **p})})
    #         # also try without any group/partition
    #         create_candidates.append({"User": with_card({**base})})


    #     # base_variants = [
    #     #     {"user_id": {"user_id": uid}, "login_id": uid, "name": display_name},
    #     #     {"user_id": uid,              "login_id": uid, "name": display_name},
    #     #     {"user_id": {"user_id": uid},                 "name": display_name},
    #     # ]
    #     # if uid.isdigit():
    #     #     pin4 = uid[-4:].rjust(4, "0")
    #     #     base_variants.append({"user_id": uid, "login_id": uid, "name": display_name, "pin": pin4})

    #     # # All the group key shapes I’ve seen
    #     # group_shapes = [{}]
    #     # if group_id is not None:
    #     #     gid = int(group_id)
    #     #     group_shapes = [
    #     #         {"user_group_id": gid},
    #     #         {"user_group_id": {"id": gid}},
    #     #         {"user_group":    {"id": gid}},
    #     #         {"user_groups":   [{"id": gid}]},     # list form
    #     #         {"user_group_ids":[{"id": gid}]},     # alt list form
    #     #     ]

    #     # # All the partition/site key shapes I’ve seen
    #     # part_shapes = [{}]
    #     # if partition_id is not None:
    #     #     pid = int(partition_id)
    #     #     part_shapes = [
    #     #         {"partition_id": pid},
    #     #         {"partition":    {"id": pid}},
    #     #         {"site_id":      pid},                # some builds use site/site_id
    #     #         {"site":         {"id": pid}},
    #     #     ]

    #     # # Build creation candidates = cross product of bases, groups, partitions (+ no-group/no-part fallback)
    #     # create_candidates = []
    #     # for base in base_variants:
    #     #     for g in group_shapes:
    #     #         for p in part_shapes:
    #     #             create_candidates.append({"User": with_card({**base, **g, **p})})
    #     #     # also try base without group/partition at all
    #     #     create_candidates.append({"User": with_card({**base})})

    #     # UPDATE path
    #     if existing and isinstance(existing, dict) and existing.get("id"):
    #         try:
    #             internal_id = str(existing["id"])
    #             update_base = {"user_id": {"user_id": uid}, "login_id": uid, "name": display_name}
    #             if group_id is not None:
    #                 update_base["user_group_id"] = int(group_id)
    #             if partition_id is not None:
    #                 update_base["partition_id"] = int(partition_id)
    #             recc._req("PUT", f"/users/{internal_id}", json={"User": with_card(update_base)})
    #             return {"id": internal_id, "user_id": uid, "name": display_name,
    #                     "card_no": str(card_no) if card_no else None}
    #         except Exception as e:
    #             resp_text = getattr(getattr(e, 'response', None), 'text', '') or str(e)
    #             raise UserError(_("Failed to update user %s on BioStar: %s") % (uid, resp_text))

    #     # CREATE path with exhaustive fallbacks
    #     last_err = None
    #     for body in create_candidates:
    #         try:
    #             resp = recc._req("POST", "/users", json=body)
    #             new_row = {}
    #             if isinstance(resp, dict) and isinstance(resp.get("User"), dict) and resp["User"].get("id"):
    #                 new_row = {"id": str(resp["User"]["id"])}
    #             if not new_row:
    #                 new_row = self._search_device_user(recc, uid) or {}
    #             return {"id": str(new_row.get("id") or ""), "user_id": uid, "name": display_name,
    #                     "card_no": str(card_no) if card_no else None}
    #         except Exception as e:
    #             last_err = e
    #             continue

    #     resp_text = getattr(getattr(last_err, 'response', None), 'text', '') or str(last_err)
    #     raise UserError(_("Failed to create user on BioStar: %s") % resp_text)


    # --------------------------
    # Button: push students -> device
    # --------------------------
    def action_push_students(self):
        """
        Push all students assigned to this device to BioStar, and ensure local biostar.user is linked.
        Uses res.partner where student_number is set and device_id == this device.
        """
        BiostarUser = self.env['biostar.user'].sudo()
        Partner = self.env['res.partner'].sudo()

        total = 0
        created = 0
        updated = 0
        linked  = 0

        for rec in self:
            # login once per device
            recc = rec._login()

            # Pull students for this device
            students = Partner.search([ ('student_number', '!=', False)]) #('device_id', '=', rec.id),
            if not students:
                continue

            for stu in students:
                uid = (stu.student_number or "").strip()
                if not uid:
                    continue
                total += 1

                # Upsert on BioStar
                # Use partner name as display name. If you also store card on partner, pass it here.
                info = rec._upsert_device_user(recc, uid, name=stu.name, card_no=False)

                if not stu.device_id:
                    stu.device_id = rec.id
                    
                # Create/Update local biostar.user and link student
                vals = {
                    "name": info["name"] or uid,
                    "card_no": info.get("card_no") or False,
                }
                bu = BiostarUser.search([('device_id', '=', rec.id), ('biostar_user_id', '=', uid)], limit=1)
                try:
                    with self.env.cr.savepoint():
                        if bu:
                            type(bu).write(bu, vals)
                            updated += 1
                        else:
                            vals.update({"device_id": rec.id, "biostar_user_id": uid})
                            bu = BiostarUser.create(vals)
                            created += 1

                        # link the student if not already
                        if not bu.student_id or bu.student_id.id != stu.id:
                            bu.student_id = stu.id
                            linked += 1
                except Exception as ex:
                    _logger.exception("Local link/create failed for student %s (%s): %s", stu.id, uid, ex)
                    self.env.cr.rollback()
                    continue

        # toast
        try:
            self.env['bus.bus']._sendone(
                self.env.user.partner_id, 'simple_notification',
                {'title': _('BioStar'),
                'message': _("Pushed students: %s total (created %s, updated %s, linked %s).") % (total, created, updated, linked),
                'sticky': False}
            )
        except Exception:
            pass

        return True

    # def _pick_valid_user_group_id(self, recc):
    #     """Return (group_id:int|None, partition_id:int|None)."""
    #     self.ensure_one()
    #     # 1) Use the admin-configured override if present and accessible
    #     if self.default_user_group_id:
    #         gid = int(self.default_user_group_id)
    #         try:
    #             detail = recc._req("GET", f"/user_groups/{gid}")  # also yields partition
    #             part = (detail or {}).get("UserGroup", {}).get("partition") or {}
    #             pid = int(self.default_partition_id) if self.default_partition_id else (int(part.get("id")) if part.get("id") is not None else None)
    #             return (gid, pid)
    #         except Exception:
    #             _logger.info("Configured group %s not accessible; falling back to discovery.", gid)

    #     # 2) Discover from /user_groups/search
    #     data = recc._req("POST", "/user_groups/search", json={"Query": {"limit": 50, "offset": 0}})
    #     rows = (data or {}).get("UserGroupCollection", {}).get("rows") or []
    #     if not rows:
    #         return (None, None)

    #     def gid_pid(row):
    #         gid = row.get("id")
    #         part = row.get("partition") or {}
    #         pid = row.get("partition_id")
    #         if pid is None and isinstance(part, dict):
    #             pid = part.get("id")
    #         return (int(gid), int(pid)) if (gid is not None and pid is not None) else (None, None)

    #     by_name = {str((r.get("name") or "")).strip().lower(): r for r in rows if isinstance(r, dict)}
    #     for want in {"all users", "default", "user", "users"}:
    #         r = by_name.get(want)
    #         if r and r.get("id") is not None:
    #             gid, pid = gid_pid(r)
    #             if gid is not None and pid is not None:
    #                 recc._req("GET", f"/user_groups/{gid}")  # verify visibility
    #                 return (gid, pid)

    #     # First verifiable row with a partition
    #     for r in rows:
    #         gid, pid = gid_pid(r)
    #         if gid is None or pid is None:
    #             continue
    #         try:
    #             recc._req("GET", f"/user_groups/{gid}")
    #             return (gid, pid)
    #         except Exception:
    #             continue
    #     return (None, None)

    # def _debug_list_user_groups(self, recc):
    #     data = recc._req("POST", "/user_groups/search", json={"Query": {"limit": 200, "offset": 0}})
    #     rows = (data or {}).get("UserGroupCollection", {}).get("rows") or []
    #     _logger.info("BioStar user_groups (%s): %s", len(rows), rows)

    # def _list_user_groups(self, recc):
    #     # v2 (New Local API)
    #     try:
    #         d = recc._req("POST", "/v2/user_groups/search", json={})
    #         rows = (d or {}).get("UserGroupCollection", {}).get("rows") or []
    #         if rows:
    #             return rows
    #     except Exception:
    #         pass
    #     # v1 fallback
    #     d = recc._req("GET", "/user_groups")
    #     coll = (d or {}).get("UserGroupCollection") or (d or {}).get("UserGroupList") or {}
    #     return coll.get("rows") or coll.get("records") or (d or {}).get("user_groups") or []

    # def _get_valid_user_group(self, recc):
    #     rows = self._list_user_groups(recc)
    #     if not rows:
    #         raise UserError("BioStar: no user groups returned by API.")
    #     # Prefer “All Users” if present
    #     g = next((r for r in rows if (r.get("name") or "").lower() == "all users"), rows[0])
    #     gid = g.get("id")
    #     part = (g.get("partition") or {}).get("id")
    #     if not gid:
    #         raise UserError("BioStar: user group has no id.")
    #     # sanity-check that BioStar accepts this id
    #     try:
    #         recc._req("POST", "/v2/user_groups/search", json={"UserGroupFilter": {"userGroupIdList": [int(gid)]}})
    #     except Exception:
    #         # not fatal; some servers are v1 only
    #         pass
    #     return int(gid), (int(part) if part not in (None, "") else None)

    def _list_user_groups(self, recc):
        # Try v2 list
        try:
            d = recc._req("POST", "/v2/user_groups/search", json={})
            rows = (d or {}).get("UserGroupCollection", {}).get("rows") or []
            if rows:
                return rows
        except Exception:
            pass
        # v1 fallback(s)
        try:
            d = recc._req("GET", "/user_groups")
            coll = (d or {}).get("UserGroupCollection") or (d or {}).get("UserGroupList") or {}
            return coll.get("rows") or coll.get("records") or (d or {}).get("user_groups") or []
        except Exception:
            return []

    def _get_valid_user_group(self, recc):
        rows = self._list_user_groups(recc)
        if not rows:
            # cannot determine any group → let create happen without one
            return (None, None)
        g = next((r for r in rows if (r.get("name") or "").lower() == "all users"), rows[0])
        gid = g.get("id")
        part = (g.get("partition") or {}).get("id")
        return (int(gid) if gid is not None else None,
                int(part) if part not in (None, "") else None)


    def _v1_create_bodies(self, uid, name, gid_try, part_try):
        U = {
            "user_id": str(uid),
            "login_id": str(uid),
            "name": name or str(uid),
            "is_active": True,
        }
        bodies = []

        # always try with no group/partition first (server may default to “All Users”)
        bodies.append({"User": dict(U)})

        if gid_try is not None and part_try is not None:
            gi, pi = int(gid_try), int(part_try)
            bodies.append({"User": {**U, "user_group": {"id": gi}, "user_group_id": gi, "partition": {"id": pi}}})

        if gid_try is not None:
            gi = int(gid_try)
            bodies += [
                {"User": {**U, "user_group": {"id": gi}}},
                {"User": {**U, "user_group_id": gi}},
                {"User": {**U, "user_groups": [{"id": gi}]}},
                {"User": {**U, "user_group_ids": [{"id": gi}]}}
            ]

        if part_try is not None:
            pi = int(part_try)
            bodies += [
                {"User": {**U, "partition": {"id": pi}}},
                {"User": {**U, "site": {"id": pi}}},
                {"User": {**U, "site_id": pi}},
            ]
        return bodies



    def _payload_user_v2(self, uid, name, gid):
        return {
            "user": {
                "userId": str(uid),
                "loginId": str(uid),              # <-- add this
                "name": name or str(uid),
                "userGroupId": int(gid),
                "isActivated": True,
            }
        }

    def _payload_user_v1(self, uid, name, gid, part):
        body = {
            "User": {
                "user_id": str(uid),
                "login_id": str(uid),               # <-- add this
                "name": name or str(uid),
                "is_active": True
                }
        }
        # v1 accepts either user_group.id OR user_group_id depending on version; cover both.
        if gid is not None:
            body["User"]["user_group"] = {"id": int(gid)}
            body["User"]["user_group_id"] = int(gid)
        if part is not None:
            body["User"]["partition"] = {"id": int(part)}
        return body

    # def _upsert_device_user(self, recc, uid, name=None, card_no=False):
    #     gid, part = self._get_valid_user_group(recc)

    #     def try_create(gid_try):
    #         # v2 first
    #         try:
    #             return recc._req("POST", "/v2/users/add", json=self._payload_user_v2(uid, name, gid_try))
    #         except Exception as e_v2:
    #             # v1 fallback
    #             return recc._req("POST", "/users", json=self._payload_user_v1(uid, name, gid_try, part))

    #     try:
    #         return try_create(gid)
    #     except Exception as e:
    #         # If BioStar says "User Group doesn't exist", retry with the first available group id.
    #         msg = str(getattr(e, "response", None) and getattr(e.response, "text", "")) or str(e)
    #         if "User Group doesn't exist" in msg or "group" in msg.lower():
    #             rows = self._list_user_groups(recc)
    #             alt = rows[0].get("id") if rows else None
    #             if alt is not None and int(alt) != int(gid):
    #                 return try_create(int(alt))
    #         raise

    # def _upsert_device_user(self, recc, uid, name=None, card_no=False):
    #     gid, part = self._get_valid_user_group(recc)

    #     def v1_shapes(gid_try, part_try):
    #         U = {
    #             "user_id": str(uid),
    #             "login_id": str(uid),
    #             "name": name or str(uid),
    #             "is_active": True,
    #         }
    #         shapes = []

    #         # group + partition
    #         if gid_try is not None and part_try is not None:
    #             shapes.append({"User": {**U,
    #                 "user_group": {"id": int(gid_try)},
    #                 "user_group_id": int(gid_try),
    #                 "partition": {"id": int(part_try)},
    #             }})

    #         # group only (several accepted variants)
    #         if gid_try is not None:
    #             gid_i = int(gid_try)
    #             shapes += [
    #                 {"User": {**U, "user_group": {"id": gid_i}}},
    #                 {"User": {**U, "user_group_id": gid_i}},
    #                 {"User": {**U, "user_groups": [{"id": gid_i}]}},
    #                 {"User": {**U, "user_group_ids": [{"id": gid_i}]}},
    #             ]

    #         # partition/site only (rarely needed, but harmless)
    #         if part_try is not None:
    #             pi = int(part_try)
    #             shapes += [
    #                 {"User": {**U, "partition": {"id": pi}}},
    #                 {"User": {**U, "site": {"id": pi}}},
    #                 {"User": {**U, "site_id": pi}},
    #             ]

    #         # last resort: let server default to All Users
    #         shapes.append({"User": {**U}})
    #         return shapes


    #     def try_create_with(gid_try, part_try):
    #         # v2 first
    #         try:
    #             v2_user = {
    #                 "userId": str(uid),
    #                 "loginId": str(uid),
    #                 "name": name or str(uid),
    #                 "isActivated": True,
    #             }
    #             if gid_try is not None:
    #                 v2_user["userGroupId"] = int(gid_try)
    #             return recc._req("POST", "/v2/users/add", json={"user": v2_user})
    #         except Exception as e_v2:
    #             # if v2 complains about group, retry v2 without group once
    #             msg = (getattr(getattr(e_v2, "response", None), "text", "") or str(e_v2)).lower()
    #             if "group" in msg and gid_try is not None:
    #                 try:
    #                     return recc._req("POST", "/v2/users/add", json={
    #                         "user": {
    #                             "userId": str(uid),
    #                             "loginId": str(uid),
    #                             "name": name or str(uid),
    #                             "isActivated": True,
    #                         }
    #                     })
    #                 except Exception:
    #                     pass

    #             # v1 fallbacks
    #             last = None
    #             for body in v1_shapes(gid_try, part_try):
    #                 try:
    #                     return recc._req("POST", "/users", json=body)
    #                 except Exception as e1:
    #                     last = e1
    #                     continue
    #             raise last

    def _upsert_device_user(self, recc, uid, name=None, card_no=False):
        uid = str(uid or "").strip()
        if not uid:
            raise UserError(_("Student number (user code) is required."))

        gid, part = self._get_valid_user_group(recc)

        def try_create_with(gid_try, part_try):
            # 1) v2 attempt (only add group field when present)
            try:
                v2_user = {"userId": str(uid), "loginId": str(uid), "name": name or str(uid), "isActivated": True}
                if gid_try is not None:
                    v2_user["userGroupId"] = int(gid_try)
                return recc._req("POST", "/v2/users/add", json={"user": v2_user})
            except Exception as e_v2:
                # if v2 unsupported or fails, continue to v1 fallbacks
                pass

            # 2) v1 attempts – start with no-group body, then group/partition variants
            last = None
            for body in self._v1_create_bodies(uid, name, gid_try, part_try):
                try:
                    return recc._req("POST", "/users", json=body)
                except Exception as e1:
                    last = e1
                    # if the server specifically says group doesn't exist, jump to no-group retry once
                    msg = (getattr(getattr(e1, "response", None), "text", "") or str(e1)).lower()
                    if "group doesn't exist" in msg:
                        # ensure we try a pure no-group body immediately
                        try:
                            return recc._req("POST", "/users", json={"User": {
                                "user_id": str(uid), "login_id": str(uid), "name": name or str(uid), "is_active": True
                            }})
                        except Exception as e2:
                            last = e2
                            break
                    continue
            raise last

        # First attempt: with discovered gid/part (they may be None → safe)
        try:
            return try_create_with(gid, part)
        except Exception as e:
            # Final safety net: force a clean no-group retry
            return try_create_with(None, None)


        # def v1_shapes(gid_try, part_try):
        #     U = {"user_id": str(uid), "login_id": str(uid), "name": name or str(uid), "is_active": True}
        #     # 1) group + partition
        #     s = [
        #         {"User": {**U, "user_group": {"id": int(gid_try)}, "user_group_id": int(gid_try),
        #                 **({"partition": {"id": int(part_try)}} if part_try is not None else {})}},
        #         # 2) group only (no partition)
        #         {"User": {**U, "user_group": {"id": int(gid_try)}, "user_group_id": int(gid_try)}},
        #         # 3) list form
        #         {"User": {**U, "user_groups": [{"id": int(gid_try)}]}},
        #         {"User": {**U, "user_group_ids": [{"id": int(gid_try)}]}},
        #         # 4) site shapes (some builds use site/site_id)
        #         {"User": {**U, "user_group": {"id": int(gid_try)},
        #                 **({"site": {"id": int(part_try)}} if part_try is not None else {})}},
        #         {"User": {**U, "user_group": {"id": int(gid_try)},
        #                 **({"site_id": int(part_try)} if part_try is not None else {})}},
        #         # 5) NO group/partition at all → let server default to “All Users”
        #         {"User": {**U}},
        #     ]
        #     return s

        # def try_create_with(gid_try, part_try):
        #     # v2 first
        #     try:
        #         return recc._req("POST", "/v2/users/add", json={
        #             "user": {
        #                 "userId": str(uid),
        #                 "loginId": str(uid),
        #                 "name": name or str(uid),
        #                 "isActivated": True,
        #                 "userGroupId": int(gid_try),
        #             }
        #         })
        #     except Exception as e_v2:
        #         # If v2 rejects group, immediately try v2 *without* group once.
        #         msg = (getattr(getattr(e_v2, "response", None), "text", "") or str(e_v2)).lower()
        #         if "group" in msg:
        #             try:
        #                 return recc._req("POST", "/v2/users/add", json={
        #                     "user": {
        #                         "userId": str(uid),
        #                         "loginId": str(uid),
        #                         "name": name or str(uid),
        #                         "isActivated": True,
        #                     }
        #                 })
        #             except Exception:
        #                 pass
        #         # v1 fallbacks (multiple shapes; last one is no group/partition)
        #         last = None
        #         for body in v1_shapes(gid_try, part_try):
        #             try:
        #                 return recc._req("POST", "/users", json=body)
        #             except Exception as e1:
        #                 last = e1
        #                 continue
        #         raise last

        try:
            return try_create_with(gid, part)
        except Exception as e:
            # If still “group” error, try again with the *first* available group id,
            # and finally with NO group/partition at all.
            msg = (getattr(getattr(e, "response", None), "text", "") or str(e)).lower()
            if "group" in msg:
                rows = self._list_user_groups(recc)
                alt = rows and rows[0].get("id")
                if alt is not None and int(alt) != int(gid):
                    try:
                        return try_create_with(int(alt), part)
                    except Exception:
                        pass
                # last resort: no group/partition
                return try_create_with(None, None)
            raise
