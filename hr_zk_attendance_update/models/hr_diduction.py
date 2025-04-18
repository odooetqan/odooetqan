from odoo import api, fields, models, tools
from datetime import datetime, timedelta




class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    deduction_multiplier = fields.Float(string='Deduction Multiplier', default=1.0)
    allowance_multiplier = fields.Float(string='Allowance Multiplier', default=1.0)
    total_wage = fields.Float(string='Total Wage')
