from odoo import http
from odoo.http import request

class PortalHrLoan(http.Controller):
    @http.route(['/my/loans'], type='http', auth="user", website=True)
    def portal_my_loans(self, **kwargs):
        user = request.env.user
        loans = request.env['hr.loan'].search([('employee_id.user_id', '=', user.id)])
        values = {
            'loans': loans,
        }
        return request.render('your_module_name.portal_hr_loan_list', values)
