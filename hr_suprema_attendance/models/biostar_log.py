# models/biostar_log.py (or in your existing file)

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from psycopg2 import IntegrityError
from datetime import timedelta

class BiostarAttendanceLog(models.Model):
    _name = "biostar.attendance.log"
    _description = "BioStar Raw Attendance Log"
    _order = "event_dt_utc asc, id asc"
    _rec_name = "event_dt_utc"

    device_id = fields.Many2one("biostar.device", required=True, index=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", index=True)
    biostar_user_id = fields.Char(index=True, required=True)
    event_dt_utc = fields.Datetime(required=True, index=True, help="UTC timestamp from BioStar")
    direction = fields.Selection([('in', 'In'), ('out', 'Out'), ('unknown', 'Unknown')],
                                 default='unknown', index=True)
    raw = fields.Json(string="Raw Payload")
    external_key = fields.Char(required=True, index=True,
                               help="Uniqueness key from device+event (e.g., device-id/user/timestamp/event_id)")
    state = fields.Selection([('draft', 'Draft'), ('processed', 'Processed'), ('skipped', 'Skipped')],
                             default='draft', index=True)
    note = fields.Char()
    attendance_id = fields.Many2one("hr.attendance", index=True, readonly=True)
    event_time = fields.Datetime("Event Time", required=True)
    event_type = fields.Char("Event Type")
    direction = fields.Selection([
        ("in", "Check In"),
        ("out", "Check Out"),
    ], string="Direction")
    raw_payload = fields.Text("Raw JSON")
    
    _sql_constraints = [
        ("uniq_external_key", "unique(external_key)",
         "This log entry already exists (duplicate external key)."),
    ]
