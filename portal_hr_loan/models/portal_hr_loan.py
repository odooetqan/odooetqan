from odoo import models, fields, api

class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    overtime_deductible = fields.Boolean(string="Overtime Deductible", default=False)


class HrLoan(models.Model):
    _inherit = 'hr.loan'


class HrSalary(models.Model):
    _name = 'hr.salary'
    _description = 'Employee Salary'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    amount = fields.Float(string='Amount', required=True)
    description = fields.Text(string='Description')
    date = fields.Date(string='Salary Date', default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft')

    additional_notes = fields.Text(string="Additional Notes")
    
    def approve_loan(self):
        """Custom method to approve loans"""
        for record in self:
            record.state = 'approved'
            # Add any additional logic here


class HrLoanLine(models.Model):
    _inherit = 'hr.loan.line'

    line_number = fields.Integer(string="Line Number")


class HRPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    bonus_percentage = fields.Float(string="Bonus Percentage", default=10.0)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_total_loan_deductions(self):
        """Calculate total loan deductions for the payslip."""
        total_deductions = sum(line.amount for line in self.input_line_ids if line.input_type_id.code == 'LOAN')
        return total_deductions


class HRPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    is_loan_related = fields.Boolean(string="Is Loan Related", default=False)


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    description = fields.Text(string="Description")


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    def compute_bonus(self, employee):
        """Compute bonus based on employee data"""
        # Add bonus computation logic here
        pass
