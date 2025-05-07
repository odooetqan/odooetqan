from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_code = fields.Char(string="Employee Code")

# In your custom module, add this extension:
class Department(models.Model):
    _inherit = 'hr.department'

    code = fields.Char(string='Code')

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_export_payslips_excel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Export Payslips to Excel',
            'res_model': 'payslip.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_ids': self.ids},
        }
