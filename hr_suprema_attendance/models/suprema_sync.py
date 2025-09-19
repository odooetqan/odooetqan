import json
import logging
from datetime import datetime, timedelta, timezone

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SupremaSync(models.Model):
    _name = "suprema.sync"
    _description = "Suprema BioStar 2 Attendance Sync"

    @api.model
    def _get_cfg(self):
        ICP = self.env["ir.config_parameter"].sudo()
        base = ICP.get_param("suprema.base_url")
        user = ICP.get_param("suprema.username")
        pwd  = ICP.get_param("suprema.password")
        verify_ssl = ICP.get_param("suprema.verify_ssl", "0") == "1"
        match_field = ICP.get_param("suprema.user_field", "barcode")
        if not base or not user or not pwd:
            raise UserError(_("Please configure BioStar 2 credentials in Settings."))
        return {
            "base": base.rstrip("/"),
            "user": user,
            "pwd":  pwd,
            "verify": verify_ssl,
            "match_field": match_field,
        }

    # ---- public entry from cron
    @api.model
    def cron_sync_attendance(self):
        cfg = self._get_cfg()
        session = requests.Session()
        session.verify = cfg["verify"]

        self._login(session, cfg)
        events = self._fetch_events(session, cfg)
        if not events:
            _logger.info("Suprema: no new events.")
            return

        self._process_events(events, cfg)

    # ---- helpers
    def _login(self, session: requests.Session, cfg):
        url = f"{cfg['base']}/api/login"
        payload = {"user_id": cfg["user"], "password": cfg["pwd"]}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        r = session.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if r.status_code != 200:
            raise UserError(_("BioStar login failed: %s") % r.text)
        # Cookie like bs-session-id is usually set automatically on the session obj
        _logger.info("Suprema: login OK, cookies: %s", r.cookies.get_dict())

    def _fetch_events(self, session: requests.Session, cfg):
        ICP = self.env["ir.config_parameter"].sudo()
        last_sync = ICP.get_param("suprema.last_sync_at")

        # default: pull last 24h on first run
        if last_sync:
            start_dt = datetime.fromisoformat(last_sync)
        else:
            start_dt = datetime.now(timezone.utc) - timedelta(days=1)

        end_dt = datetime.now(timezone.utc)

        # Example payload for search; adjust to your API shape.
        # Many BioStar installs use POST /api/events/search with {"start_time": "...", "end_time": "..."}
        url = f"{cfg['base']}/api/events/search"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        payload = {
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "limit": 1000,
            "offset": 0,
            # Optional filters: device, event types (authentication success), etc.
            # "event_type_code": [ ... ]
        }

        all_events = []
        while True:
            r = session.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if r.status_code != 200:
                raise UserError(_("BioStar events fetch failed: %s") % r.text)
            data = r.json() or {}
            chunk = data.get("events") or data.get("records") or []
            all_events.extend(chunk)

            # Pagination—adjust according to your API.
            if len(chunk) < payload["limit"]:
                break
            payload["offset"] += payload["limit"]

        # Save the cursor
        ICP.set_param("suprema.last_sync_at", end_dt.isoformat())
        _logger.info("Suprema: fetched %d events (%s → %s)", len(all_events), start_dt, end_dt)
        return all_events

    def _process_events(self, events, cfg):
        """
        Minimal logic:
        - consider "VERIFY_SUCCESS" as a punch.
        - alternate IN/OUT per employee chronologically.
        You can refine by device direction if you have explicit IN/OUT readers.
        """
        # Sort by time
        def _parse_dt(s):
            # BioStar often returns ISO8601; ensure timezone-aware
            try:
                return datetime.fromisoformat(s)
            except Exception:
                # try without tz
                return datetime.fromisoformat(s.replace("Z", "+00:00"))

        events = sorted(events, key=lambda e: _parse_dt(e.get("event_time") or e.get("date_time") or e.get("datetime")))

        Employee = self.env["hr.employee"].sudo()
        Attendance = self.env["hr.attendance"].sudo()

        # cache: user_id -> employee
        emp_cache = {}
        # cache: employee -> last open attendance (no check_out)
        open_att = {}

        # Prime open_att
        for emp in Employee.search([]):
            last = Attendance.search([("employee_id", "=", emp.id)], order="check_in desc", limit=1)
            if last and not last.check_out:
                open_att[emp.id] = last

        # Event type keys—adjust to your payload
        # Typical keys: event["event_type"], event["event_type_name"], event["code"], event["sub_code"]
        def is_punch(ev):
            et = (ev.get("event_type") or ev.get("event_type_name") or "").upper()
            # keep this broad first; refine later if you pull too many
            return "VERIFY" in et or "AUTH" in et or "ACCESS_GRANTED" in et

        def get_user_code(ev):
            # Try user_id, user_name, user_code…
            return str(ev.get("user_id") or ev.get("user") or ev.get("user_code") or "").strip()

        for ev in events:
            if not is_punch(ev):
                continue
            user_code = get_user_code(ev)
            if not user_code:
                continue

            # map BioStar user -> employee
            emp = emp_cache.get(user_code)
            if not emp:
                domain = []
                if cfg["match_field"] == "barcode":
                    domain = [("barcode", "=", user_code)]
                elif cfg["match_field"] == "work_email":
                    domain = [("work_email", "=", user_code)]
                else:
                    # custom x_suprema_user_id on hr.employee
                    domain = [("x_suprema_user_id", "=", user_code)]

                emp = Employee.search(domain, limit=1)
                if not emp:
                    _logger.warning("Suprema: no employee mapped for user %s", user_code)
                    continue
                emp_cache[user_code] = emp

            punch_dt = _parse_dt(ev.get("event_time") or ev.get("date_time") or ev.get("datetime"))

            # Simple alternate IN/OUT:
            last_open = open_att.get(emp.id)
            if not last_open:
                # create check-in
                Attendance.create({
                    "employee_id": emp.id,
                    "check_in": punch_dt,
                })
                # refresh pointer
                last_new = Attendance.search([("employee_id", "=", emp.id)], order="id desc", limit=1)
                open_att[emp.id] = last_new
            else:
                # close it
                # avoid negative / out-of-order times
                if punch_dt <= last_open.check_in:
                    _logger.info("Suprema: ignoring out-of-order punch for %s at %s", emp.name, punch_dt)
                    continue
                last_open.write({"check_out": punch_dt})
                open_att.pop(emp.id, None)

        _logger.info("Suprema: attendance sync done.")
