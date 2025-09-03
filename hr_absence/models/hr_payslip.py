# =========================
# models/hr_absence.py
# =========================
from datetime import datetime, timedelta, time as dtime
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# =========================
# Payslip integration
# =========================
class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    absence_days = fields.Integer(
        string="Absent Days",
        compute="_compute_absence_counts",
        store=False,
        help="Total days with status = Absent in this payslip range."
    )
    partial_days = fields.Integer(
        string="Partial Days",
        compute="_compute_absence_counts",
        store=False,
        help="Total days with status = Partial in this payslip range."
    )
    present_days = fields.Integer(
        string="Present Days",
        compute="_compute_absence_counts",
        store=False,
        help="Total days with status = Present in this payslip range."
    )

    @api.depends("employee_id", "date_from", "date_to")
    def _compute_absence_counts(self):
        Day = self.env["hr.attendance.dayline"]
        for slip in self:
            slip.absence_days = slip.partial_days = slip.present_days = 0
            if not slip.employee_id or not slip.date_from or not slip.date_to:
                continue
            dls = Day.search([
                ("employee_id", "=", slip.employee_id.id),
                ("date", ">=", slip.date_from),
                ("date", "<=", slip.date_to),
            ])
            slip.absence_days = sum(1 for d in dls if d.status == "absent")
            slip.partial_days = sum(1 for d in dls if d.status == "partial")
            slip.present_days = sum(1 for d in dls if d.status == "present")

    def action_push_absence_days_to_inputs(self):
        """Optional: write the 'absence_days' count into an Inputs line (code ABSENCE_DAYS)."""
        for slip in self:
            if not (slip.employee_id and slip.date_from and slip.date_to):
                raise UserError(_("Payslip must have an employee and a date range."))
            # recompute the counts (in case user didn't leave focus)
            slip._compute_absence_counts()

            # find/create Inputs line with code ABSENCE_DAYS
            line = slip.input_line_ids.filtered(lambda l: l.code == "ABSENCE_DAYS")[:1]
            vals = {
                "name": _("Absence Days"),
                "code": "ABSENCE_DAYS",
                "amount": float(slip.absence_days),
            }
            if line:
                line.write(vals)
            else:
                slip.input_line_ids = [(0, 0, vals)]
        return True
