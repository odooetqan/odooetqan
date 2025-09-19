# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlsplit, urlunsplit

import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from psycopg2 import Error as PsycoError
from psycopg2 import IntegrityError

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REQ_TIMEOUT = 60
LOGIN_TIMEOUT = 30
MAX_PAGE = 50
PAGE_LIMIT = 200
EVENT_PAGE_LIMIT = 500

EVENT_CODE_IN = {"4867"}           # Extend as needed
EVENT_CODE_OUT: set[str] = set()   # Extend as needed

# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
def _normalize_origin(u: str) -> str:
    """Return scheme://host[:port] with no path/query/fragment. Raise if invalid."""
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
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # -----------------------------------------------------------------------
    # Fields
    # -----------------------------------------------------------------------
    name = fields.Char(required=True, tracking=True)
    base_url = fields.Char(
        "API Base URL",
        required=True,
        help="Origin only (no /api). Example: https://10.201.2.88:5002",
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
        [("unknown", "Unknown"), ("ok", "OK"), ("error", "Error")],
        default="unknown",
        readonly=True,
    )
    status_message = fields.Char(readonly=True)

    user_ids = fields.One2many("biostar.user", "device_id", string="Users")

    # Student timing knobs
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

    attendance_mode = fields.Selection(
        [("employee", "Employee"), ("student", "Student")],
        string="Attendance Mode",
        default="employee",
    )

    # Defaults for creating users on device
    default_user_group_id = fields.Integer(
        string="Default User Group ID",
        help="If set, force this User Group when creating users on BioStar.",
    )
    default_partition_id = fields.Integer(
        string="Default Partition/Site ID",
        help="If set, force this Partition/Site when creating users on BioStar.",
    )

    # -----------------------------------------------------------------------
    # Internals / utilities
    # -----------------------------------------------------------------------
    def _safe_write(self, rec: "BiostarDevice", vals: Dict[str, Any]) -> bool:
        """Bypass any accidental shadowing of instance .write."""
        return type(rec).write(rec, vals)

    def _session(self) -> requests.Session:
        """Create a fresh session with standard headers."""
        s = requests.Session()
        s.verify = bool(self.verify_ssl)
        origin = _normalize_origin(self.base_url)
        s.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Odoo-BioStar/1.0",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": origin,
                "Referer": origin + "/",
            }
        )
        return s

    # ---- session/login helpers ------------------------------------------------
    def _login(self) -> "BiostarDevice":
        """Login and return a record with fresh cookies/session in its context."""
        for rec in self:
            origin = _normalize_origin(rec.base_url)
            url = _api_url(origin, "/login")
            payload = {"User": {"login_id": rec.username, "password": rec.password}}

            s = rec._session()
            r = s.post(url, json=payload, timeout=LOGIN_TIMEOUT, allow_redirects=False)

            bs_sid = r.headers.get("bs-session-id")
            ok = (r.status_code == 200) or bool(bs_sid)
            if not ok:
                raise UserError(_("Login failed (%s): %s") % (r.status_code, r.text or r.reason))

            cookies = s.cookies.get_dict()
            if bs_sid:
                cookies["bs-session-id"] = bs_sid

            self._safe_write(rec, {"token": "COOKIE", "token_expires": fields.Datetime.now() + timedelta(hours=1)})

            return rec.with_context(_cookies=cookies, _bs_sid=bs_sid or "")
        return self

    def _authed_session(self) -> Tuple[requests.Session, Dict[str, str], str]:
        """Build a session and populate cookies/bs-session-id from context (if any)."""
        s = self._session()
        cookies = dict(self.env.context.get("_cookies") or {})
        if cookies:
            s.cookies.update(cookies)
        bs_sid = self.env.context.get("_bs_sid")
        if bs_sid:
            s.headers["bs-session-id"] = bs_sid
        return s, cookies, bs_sid or ""

    def _req(self, method: str, path: str, **kw) -> Any:
        """
        Request under /api/<path>. Re-login once on 401/419.
        Returns parsed JSON dict/list when possible, else {'_raw': text} or {}.
        Raises UserError with remote body for non-2xx.
        """
        self.ensure_one()
        origin = _normalize_origin(self.base_url)
        url = _api_url(origin, path)

        s, _, _ = self._authed_session()
        r = s.request(method.upper(), url, timeout=REQ_TIMEOUT, **kw)

        if r.status_code in (401, 419):
            recc = self._login()
            s, _, _ = recc._authed_session()
            r = s.request(method.upper(), url, timeout=REQ_TIMEOUT, **kw)

        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise UserError(f"BioStar API {r.status_code} on {path}:\n{r.text}") from e

        if not r.text:
            return {}
        try:
            return r.json()
        except Exception:
            return {"_raw": r.text}

    def _req_raw(self, method: str, path: str, **kw) -> requests.Response:
        """Same as _req but returns the raw Response (for image bytes)."""
        self.ensure_one()
        origin = _normalize_origin(self.base_url)
        url = _api_url(origin, path)

        s, _, _ = self._authed_session()
        r = s.request(method.upper(), url, timeout=REQ_TIMEOUT, **kw)
        if r.status_code in (401, 419):
            recc = self._login()
            s, _, _ = recc._authed_session()
            r = s.request(method.upper(), url, timeout=REQ_TIMEOUT, **kw)
        return r

    # ---- lookups --------------------------------------------------------------
    def _get_internal_user_id(self, recc: "BiostarDevice", user_code: Union[str, int]) -> Optional[int]:
        """Return BioStar internal numeric id for a given user code (string)."""
        try:
            body = {
                "Query": {
                    "limit": 1,
                    "offset": 0,
                    "conditions": [{"column": "user_id.user_id", "operator": 0, "values": [str(user_code)]}],
                }
            }
            data = recc._req("POST", "/users/search", json=body)
            row = (data or {}).get("UserCollection", {}).get("rows") or []
            if row and isinstance(row[0], dict):
                iid = row[0].get("id")
                if iid is not None:
                    return int(str(iid))
        except Exception as e:
            _logger.info("Lookup internal id for %s failed: %s", user_code, e)
        return None

    def _fetch_biostar_user_image(
        self, recc: "BiostarDevice", internal_id: Optional[int]
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """Return (bytes, mimetype) for user photo if available, else (None, None)."""
        if internal_id is None:
            return None, None

        candidates = [
            ("GET", f"/v2/users/{internal_id}/photo"),
            ("GET", f"/users/{internal_id}/photo"),
            ("GET", f"/users/{internal_id}/profile_image"),
            ("GET", f"/users/profile_image/{internal_id}"),
            ("GET", f"/users/{internal_id}/image"),
        ]

        for method, path in candidates:
            try:
                r = recc._req_raw(method, path, stream=False)
                if r.status_code == 200:
                    ctype = (r.headers.get("Content-Type") or "").lower()
                    if ctype.startswith("image/") and r.content:
                        return r.content, ctype
                    if r.content and len(r.content) > 1000 and "image" in (r.headers.get("Content-Disposition", "") or "").lower():
                        return r.content, ctype or "application/octet-stream"
                    try:
                        if ctype.startswith("application/json") and r.text:
                            j = r.json()
                            blob = j.get("image") or (j.get("User") or {}).get("image") or (j.get("Photo") or {}).get("data")
                            if blob:
                                return base64.b64decode(blob), "image/jpeg"
                    except Exception:
                        pass
                elif r.status_code in (404, 400):
                    continue
            except Exception as e:
                _logger.info("Photo fetch failed @ %s: %s", path, e)
                continue
        return None, None

    # -----------------------------------------------------------------------
    # Public actions: images
    # -----------------------------------------------------------------------
    def action_pull_user_images(self) -> bool:
        """Fetch and set images for linked biostar.user records."""
        BiostarUser = self.env["biostar.user"].sudo()
        for rec in self:
            recc = rec._login()
            users = BiostarUser.search(
                [
                    ("device_id", "=", rec.id),
                    "|",
                    ("employee_id.image_1920", "=", False),
                    ("student_id.image_1920", "=", False),
                ]
            )
            got = set_emp = set_stu = 0
            for bu in users:
                uid = (bu.biostar_user_id or "").strip()
                if not uid:
                    continue
                iid = rec._get_internal_user_id(recc, uid)
                img, _mt = rec._fetch_biostar_user_image(recc, iid)
                if not img:
                    continue
                b64 = base64.b64encode(img).decode()
                got += 1
                if getattr(bu, "student_id", False) and bu.student_id:
                    try:
                        bu.student_id.sudo().write({"image_1920": b64})
                        set_stu += 1
                    except Exception as e:
                        _logger.info("Set student image failed (%s): %s", uid, e)
                if bu.employee_id:
                    try:
                        bu.employee_id.sudo().write({"image_1920": b64})
                        set_emp += 1
                    except Exception as e:
                        _logger.info("Set employee image failed (%s): %s", uid, e)
                    partner = bu.employee_id.sudo().address_home_id
                    if partner:
                        try:
                            partner.write({"image_1920": b64})
                        except Exception:
                            pass
            try:
                self.env["bus.bus"]._sendone(
                    self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": _("BioStar"),
                        "message": _("User photos: downloaded %s; set on %s employees, %s students.") % (got, set_emp, set_stu),
                        "sticky": False,
                    },
                )
            except Exception:
                pass
        return True

    def action_pull_one_user_image(self, user_code: Union[str, int]) -> bool:
        """Fetch and set a single user's image by BioStar user_code."""
        self.ensure_one()
        recc = self._login()
        iid = self._get_internal_user_id(recc, user_code)
        img, _mt = self._fetch_biostar_user_image(recc, iid)
        if not img:
            raise UserError(_("No image found for user code %s") % user_code)
        b64 = base64.b64encode(img).decode()

        bu = (
            self.env["biostar.user"]
            .sudo()
            .search([("device_id", "=", self.id), ("biostar_user_id", "=", str(user_code))], limit=1)
        )
        if not bu:
            raise UserError(_("No local biostar.user mapped to %s") % user_code)

        if getattr(bu, "student_id", False) and bu.student_id:
            bu.student_id.sudo().write({"image_1920": b64})
            if getattr(bu.student_id, "address_home_id", False) and bu.student_id.address_home_id:
                bu.student_id.address_home_id.sudo().write({"image_1920": b64})
        if bu.employee_id:
            bu.employee_id.sudo().write({"image_1920": b64})
            partner = bu.employee_id.sudo().address_home_id
            if partner:
                partner.write({"image_1920": b64})
        return True

    # -----------------------------------------------------------------------
    # Parsing helpers
    # -----------------------------------------------------------------------
    def _extract_users(self, payload: Any) -> List[Union[str, Dict[str, Any]]]:
        """Return a flat list of user dicts or strings from any BioStar response."""
        if payload is None:
            return []
        if isinstance(payload, str):
            s = payload.strip()
            if s and s[0] in "[{":
                try:
                    payload = json.loads(s)
                except Exception:
                    return [line.strip() for line in s.splitlines() if line.strip()]
            else:
                return [line.strip() for line in s.splitlines() if line.strip()]
        if isinstance(payload, dict) and isinstance(payload.get("Response"), dict):
            code = payload["Response"].get("code")
            if code is not None and str(code) != "0":
                _logger.warning("BioStar Response error: %s", payload["Response"])
                return []
        if isinstance(payload, dict):
            uc = payload.get("UserCollection")
            if isinstance(uc, dict) and isinstance(uc.get("rows"), list) and uc["rows"]:
                return uc["rows"]

        out: List[Union[str, Dict[str, Any]]] = []

        def looks_like_user(d: Dict[str, Any]) -> bool:
            keys = {k.lower() for k in d.keys()}
            return bool(keys & {"user_id", "id", "userid", "usercode", "user_code"}) or (
                "name" in keys or "username" in keys or "display_name" in keys
            )

        def walk(x: Any) -> None:
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

    @api.model
    def _parse_biostar_dt(self, ts: Union[str, fields.Datetime, None]) -> Union[fields.Datetime, bool]:
        """Normalize BioStar ISO strings like 2025-09-15T14:07:16.00Z to Odoo datetime."""
        if not ts:
            return False
        s = str(ts).strip().replace("T", " ")
        if s.endswith("Z"):
            s = s[:-1]
        if "." in s:
            s = s.split(".")[0]
        return fields.Datetime.from_string(s)

    # -----------------------------------------------------------------------
    # Buttons / public API
    # -----------------------------------------------------------------------
    def action_test_connection(self) -> bool:
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

    def action_import_users(self) -> bool:
        """Create/update biostar.user records from BioStar, and auto-link to employee/student."""
        BiostarUser = self.env["biostar.user"].sudo()

        for rec in self:
            recc = rec._login()
            items: List[Union[str, Dict[str, Any]]] = []
            raw_samples: List[str] = []

            # 1) Try POST /api/users/search
            try:
                limit, offset, loops = PAGE_LIMIT, 0, 0
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
                    if loops > MAX_PAGE:
                        break
            except Exception as e:
                _logger.info("POST /api/users/search failed: %s", e)

            # 2) Fallback GET /api/users
            if not items:
                try:
                    limit, offset, loops = PAGE_LIMIT, 0, 0
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
                        if loops > MAX_PAGE:
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
                    self.env["bus.bus"]._sendone(
                        self.env.user.partner_id,
                        "simple_notification",
                        {
                            "title": _("BioStar"),
                            "message": _("User import: no users returned (check API user permissions/endpoint)."),
                            "sticky": False,
                        },
                    )
                except Exception:
                    pass
                continue

            created, updated = 0, 0
            now = fields.Datetime.now()

            # Prefetch for auto-link
            try:
                uids: List[str] = []
                for u in items:
                    if isinstance(u, str):
                        uid = u.strip()
                    else:
                        uid = str(
                            u.get("user_id")
                            or u.get("id")
                            or u.get("user_code")
                            or u.get("userID")
                            or u.get("UserID")
                            or u.get("code")
                            or ""
                        ).strip()
                    if uid:
                        uids.append(uid)
                uids = list({x for x in uids if x})
                emp_map = {e.barcode: e for e in self.env["hr.employee"].sudo().search([("barcode", "in", uids)])}
                stu_map = {p.student_number: p for p in self.env["res.partner"].sudo().search([("student_number", "in", uids)])}
            except Exception:
                emp_map, stu_map = {}, {}

            for u in items:
                if isinstance(u, str):
                    uid = u.strip()
                    name = uid
                    card = None
                else:
                    uid = str(
                        u.get("user_id")
                        or u.get("id")
                        or u.get("user_code")
                        or u.get("userID")
                        or u.get("UserID")
                        or u.get("code")
                        or ""
                    ).strip()
                    name = (u.get("name") or u.get("display_name") or u.get("UserName") or uid or "").strip()
                    card = u.get("card") or u.get("card_no") or u.get("CardNo") or u.get("rfid")
                    if card is not None:
                        card = str(card).strip()

                if not uid:
                    continue

                rec_user = BiostarUser.search([("device_id", "=", rec.id), ("biostar_user_id", "=", uid)], limit=1)

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

                        emp = emp_map.get(uid) or self.env["hr.employee"].sudo().search([("barcode", "=", uid)], limit=1)
                        if emp and not rec_user.employee_id:
                            rec_user.employee_id = emp.id
                        if not emp and not getattr(rec_user, "student_id", False):
                            stu = stu_map.get(uid) or self.env["res.partner"].sudo().search([("student_number", "=", uid)], limit=1)
                            if stu:
                                rec_user.student_id = stu.id
                except Exception as ex:
                    _logger.exception("Skipping user sync row (%s): %s", uid, ex)
                    self.env.cr.rollback()
                    continue

            self._safe_write(rec, {"last_user_sync": now})
            try:
                self.env["bus.bus"]._sendone(
                    self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": _("BioStar"),
                        "message": _("User import finished. Created: %s, Updated: %s") % (created, updated),
                        "sticky": False,
                    },
                )
            except Exception:
                pass
        return True

    # -----------------------------------------------------------------------
    # Helpers for student processing
    # -----------------------------------------------------------------------
    def _device_local_date(self, rec: "BiostarDevice", dt_utc: fields.Datetime) -> fields.Date:
        local_dt = fields.Datetime.context_timestamp(rec.with_context(tz=rec.timezone or "UTC"), dt_utc)
        return fields.Date.to_date(local_dt)

    def _process_student_logs(self) -> None:
        Log = self.env["biostar.attendance.log"].sudo()
        Att = self.env["student.attendance"].sudo()
        BiostarUser = self.env["biostar.user"].sudo()
        Partner = self.env["res.partner"].sudo()

        for rec in self:
            try:
                logs = Log.search([("device_id", "=", rec.id), ("state", "=", "draft")], order="event_dt_utc")
            except Exception:
                self.env.cr.rollback()
                logs = Log.search([("device_id", "=", rec.id), ("state", "=", "draft")], order="event_dt_utc")

            if not logs:
                continue

            buckets: Dict[Tuple[int, fields.Date], List[Any]] = {}
            for lg in logs:
                uid = (lg.biostar_user_id or "").strip()
                if not uid:
                    continue

                stu = False
                try:
                    bu = BiostarUser.search(
                        [("device_id", "=", rec.id), ("biostar_user_id", "=", uid), ("student_id", "!=", False)],
                        limit=1,
                    )
                    stu = bu.student_id if bu else False
                    if not stu:
                        stu = Partner.search([("student_number", "=", uid)], limit=1)
                except Exception:
                    self.env.cr.rollback()
                    continue

                if not stu:
                    continue

                day = self._device_local_date(rec, lg.event_dt_utc)
                buckets.setdefault((stu.id, day), []).append(lg)

            for (sid, day), items in buckets.items():
                try:
                    with self.env.cr.savepoint():
                        first_dt = min(i.event_dt_utc for i in items if i.event_dt_utc)
                        vals = {"first_check_in": first_dt, "device_id": rec.id}
                        state = Att._student_status_from_checkin(rec, day, first_dt)
                        vals["state"] = state

                        att = Att.search([("student_id", "=", sid), ("attendance_date", "=", day)], limit=1)
                        if att:
                            att.write(vals)
                        else:
                            Att.create({"student_id": sid, "attendance_date": day, **vals})

                        for lg in items:
                            lg.write({"state": "processed", "note": "student"})
                except Exception as ex:
                    _logger.exception("Student processor skipped (student %s, day %s): %s", sid, day, ex)
                    self.env.cr.rollback()
                    continue

    # -----------------------------------------------------------------------
    # Event pulling
    # -----------------------------------------------------------------------
    def action_pull_events(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        user_filter: Optional[Union[str, int]] = None,
        device_filter: Optional[Union[str, int]] = None,
    ) -> bool:
        """Fetch BioStar events -> biostar.attendance.log, then process."""
        Log = self.env["biostar.attendance.log"].sudo()
        Employee = self.env["hr.employee"].sudo()
        BiostarUser = self.env["biostar.user"].sudo()

        def _rows(payload: Any) -> List[Dict[str, Any]]:
            if isinstance(payload, dict):
                ec = payload.get("EventCollection") or {}
                rows = ec.get("rows") or []
                if isinstance(rows, list):
                    return rows
            return []

        for rec in self:
            recc = rec._login()

            since_dt = fields.Datetime.from_string(since) if since else (fields.Datetime.now() - timedelta(days=365))
            until_dt = fields.Datetime.from_string(until) if until else fields.Datetime.now()

            conditions = [
                {
                    "column": "datetime",
                    "operator": 3,  # BETWEEN
                    "values": [
                        since_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        until_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    ],
                }
            ]
            if user_filter:
                conditions.append({"column": "user_id.user_id", "operator": 0, "values": [str(user_filter)]})
            if device_filter:
                conditions.append({"column": "device_id.id", "operator": 0, "values": [str(device_filter)]})

            limit = EVENT_PAGE_LIMIT
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
                            direction = "in" if code in EVENT_CODE_IN else ("out" if code in EVENT_CODE_OUT else None)

                            external_key = f"{rec.id}:{ev_id}" if ev_id else f"{rec.id}:{uid}:{dt_utc.isoformat()}"

                            emp = Employee.search([("barcode", "=", uid)], limit=1)
                            if not emp:
                                bs_user = BiostarUser.search(
                                    [("device_id", "=", rec.id), ("biostar_user_id", "=", uid), ("employee_id", "!=", False)],
                                    limit=1,
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

            self._safe_write(rec, {"last_event_sync": fields.Datetime.now()})

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
                    self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": _("BioStar"),
                        "message": _("Pulled %s new raw events; processed to attendances.") % created,
                        "sticky": False,
                    },
                )
            except Exception:
                pass
        return True

    def action_pull_events_24(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        user_filter: Optional[Union[str, int]] = None,
        device_filter: Optional[Union[str, int]] = None,
    ) -> bool:
        """Same as action_pull_events but default window is last 24h."""
        since = since or (fields.Datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        until = until or fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.action_pull_events(since=since, until=until, user_filter=user_filter, device_filter=device_filter)

    # -----------------------------------------------------------------------
    # Employee attendance processor
    # -----------------------------------------------------------------------
    def _process_logs(self) -> None:
        """Convert unprocessed biostar.attendance.log to hr.attendance with simple policies."""
        Log = self.env["biostar.attendance.log"].sudo()
        Attendance = self.env["hr.attendance"].sudo()

        for rec in self:
            if rec.attendance_mode == "student":
                continue

            try:
                logs = Log.search([("device_id", "=", rec.id), ("state", "=", "draft")], order="employee_id, event_dt_utc")
            except Exception:
                self.env.cr.rollback()
                logs = Log.search([("device_id", "=", rec.id), ("state", "=", "draft")], order="employee_id, event_dt_utc")

            if not logs:
                continue

            min_gap = timedelta(seconds=int(rec.min_gap_seconds or 60))
            max_shift = timedelta(hours=int(rec.max_shift_hours or 16))

            by_emp: Dict[int, List[Any]] = {}
            for lg in logs:
                by_emp.setdefault(lg.employee_id.id or 0, []).append(lg)

            for emp_id, items in by_emp.items():
                if not emp_id:
                    continue

                items.sort(key=lambda r: (r.event_dt_utc, r.id))
                last_att = Attendance.search([("employee_id", "=", emp_id)], order="check_in desc", limit=1)

                expect = "in" if self.prefer_first_in else "out"
                if last_att and not last_att.check_out:
                    expect = "out"

                prev_dt = None
                for lg in items:
                    try:
                        with self.env.cr.savepoint():
                            if prev_dt and (lg.event_dt_utc - prev_dt) < min_gap:
                                lg.write({"state": "skipped", "note": "Within min_gap"})
                                prev_dt = lg.event_dt_utc
                                continue

                            eff_dir = getattr(lg, "direction", False) or False
                            if not eff_dir:
                                eff_dir = expect
                                expect = "out" if eff_dir == "in" else "in"

                            if not last_att or last_att.check_out:
                                if eff_dir == "out":
                                    lg.write({"state": "skipped", "note": "Unexpected OUT"})
                                    prev_dt = lg.event_dt_utc
                                    continue
                                last_att = Attendance.create({"employee_id": emp_id, "check_in": lg.event_dt_utc})
                                lg.write({"state": "processed", "attendance_id": last_att.id})
                            else:
                                close_now = eff_dir == "out"
                                if not close_now and (lg.event_dt_utc - last_att.check_in) > max_shift:
                                    close_now = True

                                if close_now and lg.event_dt_utc > last_att.check_in:
                                    last_att.write({"check_out": lg.event_dt_utc})
                                    lg.write({"state": "processed", "attendance_id": last_att.id})
                                    last_att = Attendance.search(
                                        [("employee_id", "=", emp_id)], order="check_in desc", limit=1
                                    )
                                else:
                                    lg.write({"state": "skipped", "note": "Ignored (no close)"})

                            prev_dt = lg.event_dt_utc
                    except Exception as ex:
                        _logger.exception("Processor skipped a row (emp %s, log %s): %s", emp_id, lg.id, ex)
                        self.env.cr.rollback()
                        continue

    # -----------------------------------------------------------------------
    # Legacy helpers (kept for compatibility)
    # -----------------------------------------------------------------------
    def action_pull_logs(self, since: Optional[str] = None, until: Optional[str] = None) -> None:
        Log = self.env["biostar.attendance.log"].sudo()
        for rec in self:
            recc = rec._login()
            since_dt = fields.Datetime.from_string(since) if since else (fields.Datetime.now() - timedelta(days=1))
            until_dt = fields.Datetime.from_string(until) if until else fields.Datetime.now()

            body = {
                "Query": {
                    "limit": EVENT_PAGE_LIMIT,
                    "conditions": [
                        {
                            "column": "datetime",
                            "operator": 3,
                            "values": [
                                since_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                until_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                            ],
                        }
                    ],
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
                        Log.create(
                            {
                                "device_id": rec.id,
                                "biostar_user_id": uid,
                                "employee_id": self.env["hr.employee"].search([("barcode", "=", uid)], limit=1).id or False,
                                "event_dt_utc": dt_utc,
                                "event_time": dt_utc,
                                "event_type": str((ev.get("event_type_id") or {}).get("code") or ""),
                                "state": "draft",
                            }
                        )
                except Exception:
                    self.env.cr.rollback()
                    continue

    def process_logs(self) -> None:
        """Very old helper; kept for compatibility."""
        Log = self.env["biostar.attendance.log"].sudo()
        Attendance = self.env["hr.attendance"].sudo()

        logs = Log.search([], order="event_time asc")
        for log in logs:
            try:
                with self.env.cr.savepoint():
                    if not log.employee_id:
                        continue
                    last = Attendance.search(
                        [("employee_id", "=", log.employee_id.id)], order="check_in desc", limit=1
                    )
                    if not last or last.check_out:
                        Attendance.create({"employee_id": log.employee_id.id, "check_in": log.event_time})
                    else:
                        if log.event_time > last.check_in:
                            last.write({"check_out": log.event_time})
            except Exception:
                self.env.cr.rollback()
                continue

    # -----------------------------------------------------------------------
    # BioStar User push helpers (UPDATED)
    # -----------------------------------------------------------------------
    # --- prefer v1 list (works on your server), v2 fallback -------------------
    def _list_user_groups(self, recc):
        try:
            d = recc._req("GET", "/user_groups")
            coll = (d or {}).get("UserGroupCollection") or (d or {}).get("UserGroupList") or {}
            rows = coll.get("rows") or coll.get("records") or (d or {}).get("user_groups") or []
            if rows:
                return rows
        except Exception:
            pass
        try:
            d = recc._req("POST", "/v2/user_groups/search", json={"Query": {"limit": 100, "offset": 0}})
            return (d or {}).get("UserGroupCollection", {}).get("rows") or []
        except Exception:
            return []

    # --- robust existence probe: search first, list fallback ------------------
    def _search_device_user(self, recc, uid):
        try:
            body = {"Query": {"limit": 1, "offset": 0,
                    "conditions": [{"column": "user_id.user_id", "operator": 0, "values": [str(uid)]}]}}
            data = recc._req("POST", "/users/search", json=body)
            uc = (data or {}).get("UserCollection") or {}
            rows = uc.get("rows") or []
            if rows:
                return rows[0]
        except Exception:
            try:
                data = recc._req("GET", "/users?limit=200&offset=0")
                rows = (data or {}).get("UserCollection", {}).get("rows") or []
                for r in rows:
                    if str(r.get("user_id") or r.get("id") or "").strip() == str(uid):
                        return r
            except Exception:
                pass
        return None

    # # --- create/ensure a device user using your accepted shapes ----------------
    def _upsert_device_user(self, recc, uid, name=None, card_no=False):
        """
        Create (or ensure) a user exists on BioStar using v1 payloads the server accepts.
        - Cast user_id to int when numeric (BioStar often requires int).
        - Send both user_group_id and user_group objects.
        - Include permission.id and required datetimes.
        - Include partition if available.
        """
        uid_s = str(uid or "").strip()
        if not uid_s:
            raise UserError(_("Student number (user code) is required."))
        display = name or uid_s

        # Try to coerce to int when purely numeric (BioStar v1 often requires integer user_id)
        user_id_val = int(uid_s) if uid_s.isdigit() else uid_s

        def _probe_exists():
            return bool(self._search_device_user(recc, uid_s))

        if _probe_exists():
            return True

        gid, pid = self._get_valid_user_group(recc)
        if gid is None:
            raise UserError(_("No valid User Group found. Set 'Default User Group ID' or ensure /user_groups returns 'All Users'."))

        start_dt = "2001-01-01T00:00:00.00Z"
        expiry_dt = "2030-12-31T23:59:00.00Z"

        # Base user dict with the fields BioStar commonly validates
        U = {
            "user_id": user_id_val,                 # int when possible
            "login_id": uid_s,                      # string
            "name": display,
            "is_active": True,
            "start_datetime": start_dt,
            "expiry_datetime": expiry_dt,
            "user_group_id": {"id": int(gid)},      # REQUIRED object
            "user_group": {"id": int(gid)},         # some builds check this alias
            "permission": {"id": 1},                # many servers require this
        }
        if pid is not None:
            U["partition"] = {"id": int(pid)}

        # ----- Attempt #1: v1 single-user payload
        try:
            return recc._req("POST", "/users", json={"User": U})
        except UserError as e1:
            msg = (e1.args[0] or "").lower()
            if "already" in msg or "exists" in msg or _probe_exists():
                return True

            # ----- Attempt #2: v1 bulk payload (some firmwares validate differently)
            try:
                return recc._req("POST", "/users", json={"UserCollection": {"rows": [U]}})
            except UserError as e2:
                m2 = (e2.args[0] or "").lower()
                if "already" in m2 or "exists" in m2 or _probe_exists():
                    return True
                # Show a targeted hint with the group/ids we used
                raise UserError(
                    _("BioStar rejected the user payload (uid %s). Last error: %s\n"
                    "Hints:\n"
                    "- Ensure User Group ID %s exists and is accessible.\n"
                    "- Keep user_group_id and user_group as OBJECTS with an 'id'.\n"
                    "- Ensure user_id is an integer (we coerced it to %s).\n"
                    "- Keep start_datetime & expiry_datetime in ISO ending with .00Z.")
                    % (uid_s, e2.args[0], gid, type(user_id_val).__name__)
                )



    def _get_valid_user_group(self, recc: "BiostarDevice") -> Tuple[Optional[int], Optional[int]]:
        """Return (group_id, partition_id) preferring device overrides."""
        self.ensure_one()
        if self.default_user_group_id:
            try:
                gid = int(self.default_user_group_id)
                det = recc._req("GET", f"/user_groups/{gid}")
                part = (det or {}).get("UserGroup", {}).get("partition") or {}
                pid = (
                    int(self.default_partition_id)
                    if self.default_partition_id not in (None, "", False)
                    else (int(part.get("id")) if isinstance(part, dict) and part.get("id") is not None else None)
                )
                return gid, pid
            except Exception:
                _logger.info("Configured user group %s not accessible; will discover.", self.default_user_group_id)

        rows = self._list_user_groups(recc)
        if not rows:
            return (None, None)

        g = next((r for r in rows if (str(r.get("name") or "").lower() in {"all users", "default"})), rows[0])
        gid = g.get("id")
        part_obj = g.get("partition") or {}
        pid = part_obj.get("id") if isinstance(part_obj, dict) else None
        return (int(gid) if gid is not None else None, int(pid) if pid not in (None, "") else None)

    def _payload_user_v2(self, uid: Union[str, int], name: Optional[str], gid: int) -> Dict[str, Any]:
        return {
            "user": {
                "userId": str(uid),
                "loginId": str(uid),
                "name": name or str(uid),
                "userGroupId": int(gid),
                "isActivated": True,
            }
        }

    def _payload_user_v1(self, uid: Union[str, int], name: Optional[str], gid: Optional[int], part: Optional[int]) -> Dict[str, Any]:
        body = {"User": {"user_id": str(uid), "login_id": str(uid), "name": name or str(uid), "is_active": True}}
        if gid is not None:
            body["User"]["user_group"] = {"id": int(gid)}
            body["User"]["user_group_id"] = int(gid)
        if part is not None:
            body["User"]["partition"] = {"id": int(part)}
        return body

    # -----------------------------------------------------------------------
    # Push (Users tab)
    # -----------------------------------------------------------------------
    def action_push_students(self) -> bool:
        """
        Push users from the Users tab:
          - If line has a linked student -> use student_number
          - Else if line has a linked employee -> use barcode
        Ensures a local biostar.user exists and links back.
        """
        BiostarUser = self.env["biostar.user"].sudo()
        total = created = updated = linked = 0

        for rec in self:
            recc = rec._login()
            for line in rec.user_ids:
                uid: Optional[str] = None
                display_name = line.name or ""
                if line.student_id and line.student_id.student_number:
                    uid = str(line.student_id.student_number).strip()
                    display_name = line.student_id.name or display_name
                elif line.employee_id and line.employee_id.barcode:
                    uid = str(line.employee_id.barcode).strip()
                    display_name = line.employee_id.name or display_name
                else:
                    continue

                if not uid:
                    continue

                total += 1
                rec._upsert_device_user(recc, uid, name=display_name, card_no=False)

                vals = {"name": display_name}
                bu = BiostarUser.search([("device_id", "=", rec.id), ("biostar_user_id", "=", uid)], limit=1)
                with self.env.cr.savepoint():
                    if bu:
                        type(bu).write(bu, vals)
                        updated += 1
                    else:
                        vals.update({"device_id": rec.id, "biostar_user_id": uid})
                        bu = BiostarUser.create(vals)
                        created += 1
                    if line.student_id and not bu.student_id:
                        bu.student_id = line.student_id.id
                        linked += 1
                    if line.employee_id and not bu.employee_id:
                        bu.employee_id = line.employee_id.id
                        linked += 1

        try:
            self.env["bus.bus"]._sendone(
                self.env.user.partner_id,
                "simple_notification",
                {
                    "title": _("BioStar"),
                    "message": _("Pushed users: %s total (created %s, updated %s, linked %s).") % (total, created, updated, linked),
                    "sticky": False,
                },
            )
        except Exception:
            pass
        return True


    def action_prepare_students(self) -> bool:
        """
        For each res.partner with a student_number:
        - ensure a biostar.user line exists for this device
        - link student
        - set name = partner.name, card_no = student_number, biostar_user_id = student_number
        Does NOT push to device (use 'Push Users' after preparing).
        """
        BiostarUser = self.env["biostar.user"].sudo()
        Partner = self.env["res.partner"].sudo()

        for rec in self:
            # Fetch all students that have a student_number
            students = Partner.search([("student_number", "!=", False)])
            if not students:
                continue

            # Prefetch existing device users for speed
            existing = BiostarUser.search([("device_id", "=", rec.id)])
            by_uid = {bu.biostar_user_id: bu for bu in existing if bu.biostar_user_id}

            created = updated = linked = skipped = 0

            for p in students:
                uid = str(p.student_number or "").strip()
                if not uid:
                    skipped += 1
                    continue

                vals = {
                    "name": p.name or uid,
                    "card_no": uid,               # your requirement
                }

                bu = by_uid.get(uid)
                try:
                    with self.env.cr.savepoint():
                        if bu:
                            # update values and link
                            write_vals = dict(vals)
                            if not getattr(bu, "student_id", False):
                                write_vals["student_id"] = p.id
                                linked += 1
                            type(bu).write(bu, write_vals)
                            updated += 1
                        else:
                            # create new line
                            create_vals = {
                                "device_id": rec.id,
                                "biostar_user_id": uid,
                                "student_id": p.id,
                                **vals,
                            }
                            bu = BiostarUser.create(create_vals)
                            by_uid[uid] = bu
                            created += 1
                            linked += 1
                except Exception:
                    self.env.cr.rollback()
                    skipped += 1
                    continue

            # Toast / bus message
            try:
                self.env["bus.bus"]._sendone(
                    self.env.user.partner_id,
                    "simple_notification",
                    {
                        "title": _("BioStar"),
                        "message": _(
                            "Prepared students: created %(c)s, updated %(u)s, linked %(l)s, skipped %(s)s."
                        ) % {"c": created, "u": updated, "l": linked, "s": skipped},
                        "sticky": False,
                    },
                )
            except Exception:
                pass

        return True

