# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PAvcxRTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models, fields, api


class HrEmployee(models.Model):
    """Inherit the model to add field"""
    _inherit = 'hr.employee'


    device_id_num = fields.Char(string='Biometric Device ID',
                                help="Give the biometric device id")
    deduction_multiplier = fields.Float(string='Deduction Multiplier', default=1.0)
    allowance_multiplier = fields.Float(string='Allowance Multiplier', default=1.0)
    per_minute_rate = fields.Float(string='Per Minute Rate', compute='_compute_per_minute_rate')


    @api.depends('contract_id', 'contract_id.wage', 'contract_id.resource_calendar_id.hours_per_day')
    def _compute_per_minute_rate(self):
        for employee in self:
            if employee.contract_id and employee.contract_id.resource_calendar_id:
                daily_minutes = employee.contract_id.resource_calendar_id.hours_per_day * 60
                employee.per_minute_rate = employee.contract_id.wage / daily_minutes if daily_minutes else 0.0


class HrContractHistory(models.Model):
    _inherit = "hr.contract.history"
    _description = "HR Contract History"

    time_credit = fields.Float(string="Time Credit")  # Check if this exists
