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
        sheet.write(0, 0, "Establishment ID", bold)
        sheet.write(0, 1, "1802679", bold)
        sheet.write(0, 2, "Alrajhi Bank WPS Payroll Payments Upload File", bold)
        

        sheet.write(1, 0, "Debit Account:", bold)
        sheet.write(1, 1, "SA5780000242608016004614", bold)
        sheet.write(1, 2, "Notes: Template used for upload of WPS Payroll data", bold)

        sheet.write(2, 0, "MOL ID", bold)
        sheet.write(2, 1, "10-1802679", bold)
        sheet.write(2, 2, "ملاحظة مهمة : الرجاء عدم تغيير عرض الخلايا نهائيا أو أي تغيير في القائمة مع الكتابة فقط باللغة الانجليزية وبدون استخدام أي من الفواصل او النقط اةو الاقواس ", bold)

        sheet.write(3, 0, "Payment Purpose", bold)
        sheet.write(3, 0, "Payroll", bold)

        sheet.write(4, 0, "Company Remarks", bold)
        sheet.write(4, 0, "Payroll	         ", bold)
        # -----------------------------
        # Row 6: Column headers (fields)
        # -----------------------------
        headers = [
            'Bank Name',
            'Account Number(34N)',
            # 'الرقم القومي', 
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
            'Employee Remarks'
            # 'من', 
            # 'إلى',
            # 'كود الإدارة',
            # 'الوظيفة',

        ]
        for col, header in enumerate(headers):
            sheet.write(5, col, header, bold)

        
        headers_ar = [
            'اسم البنك',
            'رقم الحساب',
            'اسم الموظف', 
            'كود الموظف ', 
            'الهوية',
            'صافي المرتب',
            'الرتب الاساسي',
            'بدل السكن',
            'اضافي ',
            'الخصومات',
            'ملاحظات الموظف '
        ]
        for col, header_ar in enumerate(headers_ar):
            sheet.write(6, col, header_ar, bold)


        # -----------------------------
        # Row 8+: Data rows
        # -----------------------------
        for row_index, slip in enumerate(payslips, start=6):  # start at row 8 (index 7)
            emp = slip.employee_id
            sheet.write(row_index, 0, emp.bank_account_id.bank_id.name if emp.bank_account_id and emp.bank_account_id.bank_id else '')
            sheet.write(row_index, 1, emp.bank_account_id.acc_number or '')
            sheet.write(row_index, 2, emp.name or '')
            sheet.write(row_index, 3, emp.employee_code or '')
            sheet.write(row_index, 4, emp.identification_id or '')
            sheet.write(row_index, 5, slip.net_wage or 0.0)
            sheet.write(row_index, 6, slip.basic or 0.0)
            sheet.write(row_index, 7, slip.Howcing_allowance or 0.0)
            sheet.write(row_index, 8, slip.other or 0.0)
            sheet.write(row_index, 9, slip.deductions or 0.0)
            sheet.write(row_index, 10, slip.note or 0.0)


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

