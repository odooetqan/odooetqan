from odoo import model

class HrLoan(models.Model):
    _inherit = 'hr.loan'    

class HrLoanLine(models.Model):
    _inherit = 'hr.loan.line'    

class HRpayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'    

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'    

class HRPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'    

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'    

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'    
