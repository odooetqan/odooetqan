
import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta  # ✅ Ensure timedelta is imported
from pytz import timezone, utc  # ✅ Import timezone functions


class HrContract(models.Model):
    _inherit = 'hr.contract'

    penalty_per_minute = fields.Float(string="Penalty Per Minute", help="Amount deducted per minute of lateness")



class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    total_late_minutes = fields.Float(string="Total Lateness (Minutes)", compute="_compute_attendance_data", store=True)
    total_overtime_minutes = fields.Float(string="Total Overtime (Minutes)", compute="_compute_attendance_data", store=True)

    lateness_deduction = fields.Float(string="Lateness Deduction", compute="_compute_lateness_deduction", store=True)
# class HrPayslip(models.Model):
#     _inherit = 'hr.payslip'

    # lateness_deduction = fields.Float(string="Lateness Deduction", compute="_compute_lateness_deduction", store=True)

    # @api.depends('employee_id', 'date_from', 'date_to')
    # def _compute_lateness_deduction(self):
    #     """Calculate total lateness deduction for each shift in the payslip period."""
    #     for payslip in self:
    #         if not payslip.employee_id:
    #             payslip.lateness_deduction = 0
    #             continue

    #         # Fetch all attendance records within the payslip period
    #         attendances = self.env['hr.attendance'].search([
    #             ('employee_id', '=', payslip.employee_id.id),
    #             ('check_in', '>=', payslip.date_from),
    #             ('check_in', '<=', payslip.date_to)
    #         ])

    #         total_deduction = 0
    #         contract = payslip.contract_id
    #         penalty_per_minute = contract.penalty_per_minute if contract and contract.penalty_per_minute else 0

    #         for att in attendances:
    #             # Calculate lateness deduction per shift
    #             shift_deduction = att.late_minutes * penalty_per_minute
    #             total_deduction += shift_deduction

    #         payslip.lateness_deduction = total_deduction

    
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_lateness_deduction(self):
        """Calculate total lateness deduction for the payslip period."""
        for payslip in self:
            if not payslip.employee_id:
                payslip.lateness_deduction = 0
                continue

            # Fetch all attendance records within the payslip period
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('check_in', '>=', payslip.date_from),
                ('check_in', '<=', payslip.date_to)
            ])

            total_late_minutes = sum(att.late_minutes for att in attendances)

            # Fetch penalty rate per minute from employee contract (or set a default)
            contract = payslip.contract_id
            penalty_per_minute = contract.penalty_per_minute if contract and contract.penalty_per_minute else 0  

            payslip.lateness_deduction = total_late_minutes * penalty_per_minute


    
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_attendance_data(self):
        """Calculate total lateness and overtime for the payslip period."""
        for payslip in self:
            if not payslip.employee_id:
                payslip.total_late_minutes = 0
                payslip.total_overtime_minutes = 0
                continue

            attendance_records = self.env['hr.attendance'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('check_in', '>=', payslip.date_from),
                ('check_out', '<=', payslip.date_to)
            ])

            payslip.total_late_minutes = sum(att.late_minutes for att in attendance_records)
            payslip.total_overtime_minutes = sum(att.overtime_minutes for att in attendance_records)
