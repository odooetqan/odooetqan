# -*- coding: utf-8 -*-
import logging
import json
import requests
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from psycopg2 import IntegrityError, Error as PsycoError

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

    # policy knobs for processing logs -> hr.attendance
    min_gap_seconds = fields.Integer(default=60, help="Ignore repeated punches within this gap.")
    max_shift_hours = fields.Integer(default=16, help="Auto close a shift longer than this.")
    prefer_first_in = fields.Boolean(default=True, help="If direction unknown, alternate starting with IN.")

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

        r.raise_for_status()
        if not r.text:
            return {}
        try:
            return r.json()
        except Exception:
            return {"_raw": r.text}

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
        # Keep date+time, drop trailing Z and fractional seconds
        s = s.replace("T", " ")
        if s.endswith("Z"):
            s = s[:-1]
        if "." in s:
            s = s.split(".")[0]
        # Odoo accepts '%Y-%m-%d %H:%M:%S'
        return fields.Datetime.from_string(s)

    # --------------------------
    # Buttons / public API
    # --------------------------
    def action_test_connection(self):
        for rec in self:
            try:
                recc = rec._login()
                # Prefer a permissive endpoint first
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
        """Create/update biostar.user records from BioStar."""
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
                    if loops > 50:  # safety
                        break
            except Exception as e:
                _logger.info("POST /api/users/search failed: %s", e)

            # 2) Fallback GET /api/users?limit=&offset=
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

                if rec_user:
                    type(rec_user).write(rec_user, vals)  # safe write
                    updated += 1
                else:
                    vals.update({"device_id": rec.id, "biostar_user_id": uid})
                    BiostarUser.create(vals)
                    created += 1

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

    def action_pull_events(self, since=None, until=None, user_filter=None, device_filter=None):
        """Fetch BioStar events (EventCollection.rows) -> biostar.attendance.log, then process."""
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

        # map codes to directions (tune to your site)
        CODE_IN  = {"4867"}  # e.g. auth success -> IN
        CODE_OUT = set()     # put OUT codes here if you have them

        for rec in self:
            recc = rec._login()

            # default window = last 24h
            since_dt = fields.Datetime.from_string(since) if since else (fields.Datetime.now() - timedelta(days=360))
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
                        "offset": offset,  # some builds ignore; loop stops on len<limit anyway
                        "conditions": conditions,
                        "orders": [{"column": "datetime", "descending": False}],
                    }
                }
                data = recc._req("POST", "/events/search", json=body)
                rows = _rows(data)
                if not rows:
                    break

                for ev in rows:
                    # --- normalize from EventCollection.rows ---
                    ev_id = str(ev.get("id") or "").strip()

                    # prefer UTC from server_datetime; fallback to local datetime
                    ts = ev.get("server_datetime") or ev.get("datetime")
                    dt_utc = self._parse_biostar_dt(ts)
                    if not dt_utc:
                        continue

                    # nested user id
                    uid = ""
                    u = ev.get("user_id") or {}
                    if isinstance(u, dict):
                        uid = str(u.get("user_id") or "").strip()
                    if not uid:
                        uid = str(ev.get("user_id") or ev.get("user_code") or "").strip()
                    if not uid:
                        continue

                    # direction from code (optional)
                    code = str((ev.get("event_type_id") or {}).get("code") or "").strip()
                    direction = "in" if code in CODE_IN else ("out" if code in CODE_OUT else None)

                    # unique key
                    external_key = f"{rec.id}:{ev_id}" if ev_id else f"{rec.id}:{uid}:{dt_utc.isoformat()}"

                    # employee mapping
                    # Guard against aborted tx: everything inside savepoint below
                    try:
                        with self.env.cr.savepoint():
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
                                "event_dt_utc": dt_utc,   # keep UTC (your processor orders by this)
                                "event_time": dt_utc,     # required by your model
                                "event_type": code,
                                "external_key": external_key,
                                "state": "draft",
                            }
                            if direction in ("in", "out"):
                                vals["direction"] = direction
                            # do NOT set 'unknown' if selection disallows it; omit instead

                            # Avoid full-row exception storm: rely on unique index and catch it.
                            Log.create(vals)
                            created += 1
                    except IntegrityError as ex:
                        # duplicate unique constraint -> already imported
                        if "uniq_external_key" in str(ex).lower():
                            continue
                        raise
                    except PsycoError:
                        # any other pg error inside the savepoint → skip this row, keep loop alive
                        continue
                    except Exception as ex:
                        # Unexpected business error: log and continue with next row
                        _logger.exception("Failed to import BioStar event %s: %s", external_key, ex)
                        continue

                if len(rows) < limit:
                    break
                offset += limit

            # watermark + process into hr.attendance
            rec.write({"last_event_sync": fields.Datetime.now()})
            self._process_logs()

            # optional notification (ignore websocket errors if bus not configured)
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

    def _process_logs(self):
        """Convert unprocessed biostar.attendance.log to hr.attendance with simple policies."""
        Log = self.env['biostar.attendance.log'].sudo()
        Attendance = self.env['hr.attendance'].sudo()

        for rec in self:
            domain = [('device_id', '=', rec.id), ('state', '=', 'draft')]
            logs = Log.search(domain, order="employee_id, event_dt_utc")
            if not logs:
                continue

            min_gap = timedelta(seconds=int(rec.min_gap_seconds or 60))
            max_shift = timedelta(hours=int(rec.max_shift_hours or 16))

            by_emp = {}
            for lg in logs:
                by_emp.setdefault(lg.employee_id.id or 0, []).append(lg)

            for emp_id, items in by_emp.items():
                if not emp_id:
                    for lg in items:
                        lg.write({'state': 'skipped', 'note': 'No employee mapping'})
                    continue

                items.sort(key=lambda r: (r.event_dt_utc, r.id))
                last_att = Attendance.search([('employee_id', '=', emp_id)], order='check_in desc', limit=1)

                expect = 'in' if self.prefer_first_in else 'out'
                if last_att and not last_att.check_out:
                    expect = 'out'

                prev_dt = None
                for lg in items:
                    if prev_dt and (lg.event_dt_utc - prev_dt) < min_gap:
                        lg.write({'state': 'skipped', 'note': 'Within min_gap'})
                        continue

                    eff_dir = getattr(lg, 'direction', False) or False
                    if not eff_dir:
                        # If direction is missing, alternate
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
                uid = str(((ev.get("user_id") or {}).get("user_id") or ev.get("user_code") or "")).strip()
                ts = ev.get("server_datetime") or ev.get("datetime")
                if not uid or not ts:
                    continue
                dt_utc = self._parse_biostar_dt(ts)
                # Use only fields you know exist on the model:
                Log.create({
                    "device_id": rec.id,
                    "biostar_user_id": uid,
                    "employee_id": self.env["hr.employee"].search([("barcode", "=", uid)], limit=1).id or False,
                    "event_dt_utc": dt_utc,
                    "event_time": dt_utc,
                    "event_type": str((ev.get("event_type_id") or {}).get("code") or ""),
                    "state": "draft",
                })

    def process_logs(self):
        Log = self.env["biostar.attendance.log"].sudo()
        Attendance = self.env["hr.attendance"].sudo()

        logs = Log.search([], order="event_time asc")
        for log in logs:
            if not log.employee_id:
                continue
            last = Attendance.search([("employee_id", "=", log.employee_id.id)], order="check_in desc", limit=1)
            if not last or last.check_out:
                Attendance.create({"employee_id": log.employee_id.id, "check_in": log.event_time})
            else:
                if log.event_time > last.check_in:
                    last.write({"check_out": log.event_time})
