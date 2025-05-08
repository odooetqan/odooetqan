from odoo import models, fields, api

class ResourceCalendarMulti(models.Model):
    _name = 'resource.calendar.multi'
    _description = 'Multi Resource Calendar'

    name = fields.Char(string="Name", required=True)
    calendar_id = fields.Many2one('resource.calendar', string="Calendar")
    employee_ids = fields.Many2many('hr.employee', string="Employees")


    def _apply_calendar_to_employees(self):
        for record in self:
            if record.calendar_id and record.employee_ids:
                _logger.info(f"Applying calendar {record.calendar_id.name} to employees: {[e.name for e in record.employee_ids]}")
                record.employee_ids.write({'resource_calendar_id': record.calendar_id.id})



    def _apply_calendar_to_employees(self):
        for record in self:
            if record.calendar_id and record.employee_ids:
                record.employee_ids.write({'resource_calendar_id': record.calendar_id.id})

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._apply_calendar_to_employees()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._apply_calendar_to_employees()
        return res