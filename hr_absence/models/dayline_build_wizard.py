# models/dayline_build_wizard.py
from datetime import timedelta
from odoo import api, fields, models, _

class DaylineBuildWizard(models.TransientModel):
    _name = "hr.dayline.build.wizard"
    _description = "Build Attendance Daylines"

    date_from = fields.Date(required=True, default=lambda self: fields.Date.today() - timedelta(days=1))
    date_to   = fields.Date(required=True,   default=lambda self: fields.Date.today() - timedelta(days=1))
    employee_ids = fields.Many2many("hr.employee", string="Employees (empty = all)")

    def _do_build(self, dfrom, dto):
        Day = self.env["hr.attendance.dayline"]
        employees = self.employee_ids if self.employee_ids else None
        Day.build_for_range(dfrom, dto, employees=employees)
        # open the listing filtered to the range
        return {
            "type": "ir.actions.act_window",
            "name": _("Attendance Daylines"),
            "res_model": "hr.attendance.dayline",
            "view_mode": "tree,graph,pivot,form",
            "domain": [("date", ">=", dfrom), ("date", "<=", dto)],
            "target": "current",
        }

    def action_build_custom(self):
        self.ensure_one()
        return self._do_build(self.date_from, self.date_to)

    def action_build_yesterday(self):
        d = fields.Date.today() - timedelta(days=1)
        return self._do_build(d, d)

    def action_build_last_365(self):
        dto = fields.Date.today() - timedelta(days=1)
        dfrom = dto - timedelta(days=364)
        return self._do_build(dfrom, dto)
