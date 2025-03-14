from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


# class PortalHrLoan(http.Controller):
#     @http.route(['/my/loans'], type='http', auth="user", website=True)
#     def portal_my_loans(self, **kwargs):
#         user = request.env.user
#         loans = request.env['hr.loan'].search([('employee_id.user_id', '=', user.id)])
#         values = {
#             'loans': loans,
#         }
#         return request.render('portal_hr_loan.portal_hr_loan_list', values)
# from odoo import http
# from odoo.http import request

class PortalHrLoan(http.Controller):

    @http.route('/my/loans', type='http', auth="user", website=True)
    def portal_loans(self, **kwargs):
        loans = request.env['hr.loan'].sudo().search([('employee_id.user_id', '=', request.env.user.id)])
        return request.render('portal_hr_loan.portal_hr_loan_list', {'loans': loans})

    @http.route('/my/loans/new', type='http', auth="user", website=True)
    def portal_create_loan(self, **kwargs):
        return request.render('portal_hr_loan.portal_create_loan_form', {})

    # @http.route('/my/loans/save', type='http', auth="user", methods=['POST'], website=True, csrf=True)
    # def portal_save_loan(self, **kwargs):
    #     request.env['hr.loan'].sudo().create({
    #         'employee_id': request.env.user.employee_id.id,
    #         'loan_amount': kwargs.get('loan_amount'),
    #         'installment': kwargs.get('installment'),
    #         'state': 'draft',
    #     })
    #     return request.redirect('/my/loans')
    
    @http.route('/my/loans/save', type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_save_loan(self, **kwargs):
        request.env['hr.loan'].sudo().create({
            'employee_id': request.env.user.employee_id.id,
            'loan_amount': kwargs.get('loan_amount'),
            'installment': kwargs.get('installment'),
            'state': 'draft',
        })
        return request.redirect('/my/loans')


    @http.route('/my/salaries', type='http', auth="user", website=True)
    def portal_salaries(self, **kwargs):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        
        _logger.info("User ID: %s", request.env.user.id)
        _logger.info("Employee ID: %s", employee.id if employee else "No employee found")
        
        if not employee:
            return request.render('portal_hr_loan.portal_hr_salary_list', {'salaries': []})
        
        salaries = request.env['hr.salary'].sudo().search([('employee_id', '=', employee.id)])

        _logger.info("Salaries: %s", salaries)

        return request.render('portal_hr_loan.portal_hr_salary_list', {'salaries': salaries})







# class PortalHrSalary(http.Controller):

#     @http.route('/my/salaries', type='http', auth="user", website=True)
#     def portal_salaries(self, **kwargs):
#         salaries = request.env['hr.salary'].sudo().search([('employee_id.user_id', '=', request.env.user.id)])
#         return request.render('portal_hr_loan.portal_hr_salary_list', {'salaries': salaries})

#     @http.route('/my/salaries/new', type='http', auth="user", website=True)
#     def portal_create_salary(self, **kwargs):
#         return request.render('portal_hr_loan.portal_create_salary_form', {})

#     @http.route('/my/salaries/save', type='http', auth="user", methods=['POST'], website=True, csrf=True)
#     def portal_save_salary(self, **kwargs):
#         request.env['hr.salary'].sudo().create({
#             'employee_id': request.env.user.employee_id.id,
#             'amount': kwargs.get('amount'),
#             'description': kwargs.get('description'),
#             'state': 'draft',
#         })
#         return request.redirect('/my/salaries')