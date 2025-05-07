from odoo import models, fields, api
import base64
import io
import xlsxwriter

class PayslipExportWizard(models.TransientModel):
    _name = 'payslip.export.wizard'
    _description = 'Wizard to export payslips to Excel'

    file_data = fields.Binary("Excel File", readonly=True)
    file_name = fields.Char("File Name", readonly=True)

    def generate_excel(self):
        selected_ids = self.env.context.get('active_ids')
        payslips = self.env['hr.payslip'].browse(selected_ids)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Payslips")

        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

        # ----------------------------
        # Row 1 to 6: Constant headers
        # ----------------------------
        sheet.write(0, 0, "جهة الصرف: البنك الأجنبي", bold)
        sheet.write(0, 1, "جهة الصرف: البنك الأجنبي", bold)
        sheet.write(1, 0, "نوع الملف: مرتبات", bold)
        sheet.write(2, 0, "الشهر: مايو 2025", bold)
        sheet.write(3, 0, "العملة: جنيه مصري", bold)
        sheet.write(4, 0, "مسؤول الملف: قسم الموارد البشرية", bold)
        sheet.write(5, 0, "تاريخ الإنشاء: 05/05/2025", bold)

        # -----------------------------
        # Row 7: Column headers (fields)
        # -----------------------------
        headers = [
            'Bank Name',
            'Account Number(34N)',
            'الرقم القومي', 
            'Employee Name', 
            'Employee Number', 
            'National ID Number (15N)',
            # 'رقم الحساب البنكي',
            # 'اسم البنك', 
            'Salary (15N)',
            'Basic Salary',
            'Housing Allowance',
            'Other Earnings',
            'Deductions',
            'Deductions',
            'Employee Remarks'
            # 'من', 
            # 'إلى',
            # 'كود الإدارة',
            # 'الوظيفة',

        ]
        for col, header in enumerate(headers):
            sheet.write(6, col, header, bold)

        # -----------------------------
        # Row 8+: Data rows
        # -----------------------------
        for row_index, slip in enumerate(payslips, start=7):  # start at row 8 (index 7)
            emp = slip.employee_id
            sheet.write(row_index, 0, emp.identification_id or '')
            sheet.write(row_index, 1, emp.name or '')
            sheet.write(row_index, 2, emp.employee_code or '')
            sheet.write(row_index, 3, emp.bank_account_id.acc_number or '')
            sheet.write(row_index, 4, emp.bank_account_id.bank_id.name if emp.bank_account_id and emp.bank_account_id.bank_id else '')
            sheet.write(row_index, 5, slip.net_wage or 0.0)
            sheet.write(row_index, 6, str(slip.date_from))
            sheet.write(row_index, 7, str(slip.date_to))
            sheet.write(row_index, 8, emp.department_id.code or '')
            sheet.write(row_index, 9, emp.job_id.name or '')

        workbook.close()
        output.seek(0)

        self.write({
            'file_data': base64.b64encode(output.read()),
            'file_name': 'تقرير_الرواتب.xlsx',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payslip.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }



    # def generate_excel(self):
    #     selected_ids = self.env.context.get('active_ids')
    #     payslips = self.env['hr.payslip'].browse(selected_ids)

    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output)
    #     sheet = workbook.add_worksheet("Payslips")

    #     # Header (Based on your uploaded template, simplified)
    #     headers = ['Employee', 'Date From', 'Date To', 'Net Wage', 'Bank Account']
    #     for col, header in enumerate(headers):
    #         sheet.write(0, col, header)

    #     # Data Rows
    #     for row, slip in enumerate(payslips, start=1):
    #         sheet.write(row, 0, slip.employee_id.name)
    #         sheet.write(row, 1, str(slip.date_from))
    #         sheet.write(row, 2, str(slip.date_to))
    #         sheet.write(row, 3, slip.net_wage)
    #         sheet.write(row, 4, slip.employee_id.bank_account_id.acc_number or '')

    #     workbook.close()
    #     output.seek(0)

    #     # Save in wizard
    #     self.write({
    #         'file_data': base64.b64encode(output.read()),
    #         'file_name': 'Payslip_Export.xlsx',
    #     })

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'payslip.export.wizard',
    #         'view_mode': 'form',
    #         'res_id': self.id,
    #         'target': 'new',
    #     }
