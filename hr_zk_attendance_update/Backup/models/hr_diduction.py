from odoo import api, fields, models, tools
from datetime import datetime, timedelta




class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    deduction_multiplier = fields.Float(string='Deduction Multiplier', default=1.0)
    allowance_multiplier = fields.Float(string='Allowance Multiplier', default=1.0)
    # per_minute_rate = fields.Float(string='Per Minute Rate', compute='_compute_per_minute_rate')
    total_wage = fields.Float(string='Total Wage')

    # @api.depends('contract_id', 'contract_id.wage', 'contract_id.resource_calendar_id.hours_per_day')
    # def _compute_per_minute_rate(self):
    #     for employee in self:
    #         if employee.contract_id and employee.contract_id.resource_calendar_id:
    #             daily_minutes = employee.contract_id.resource_calendar_id.hours_per_day * 60
    #             employee.per_minute_rate = employee.total_wage /(30*8*60)
    #             #  / daily_minutes if daily_minutes else 0.0

