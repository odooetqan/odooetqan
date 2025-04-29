from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class PortalHrLoan(http.Controller):

    # @http.route('/my/loans', type='http', auth="user", website=True)
    # def portal_loans(self, **kwargs):
    #     loans = request.env['hr.loan'].sudo().search([('employee_id.user_id', '=', request.env.user.id)])
    #     return request.render('portal_hr_loan.portal_hr_loan_tree', {'loans': loans})


    @http.route('/my/loans', type='http', auth='user', website=True)
    def portal_loans(self, **kw):
        loans = request.env['hr.loan'].search([('employee_id.user_id', '=', request.uid)])
        return request.render("portal_hr_loan.portal_hr_loan_tree", {'loans': loans})

    @http.route('/my/loans/new', type='http', auth="user", website=True)
    def portal_create_loan(self, **kwargs):
        return request.render('portal_hr_loan.portal_create_loan_form', {})

    @http.route('/my/loans/save', type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_save_loan(self, **kwargs):
        request.env['hr.loan'].sudo().create({
            'employee_id': request.env.user.employee_id.id,
            'loan_amount': kwargs.get('loan_amount'),
            'installment': kwargs.get('installment'),
            'state': 'draft',
        })
        return request.redirect('/my/loans')

#-------------------------------- Salaries -------------------------------------
    @http.route('/my/salaries', type='http', auth="user", website=True)
    def portal_salaries(self, **kwargs):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        
        _logger.info("User ID: %s", request.env.user.id)
        _logger.info("Employee ID: %s", employee.id if employee else "No employee found")
        
        if not employee:
            return request.render('portal_hr_loan.portal_hr_salary_tree', {'salaries': []})
        
        salaries = request.env['hr.payslip'].sudo().search([('employee_id', '=', employee.id)])

        _logger.info("Salaries: %s", salaries)

        return request.render('portal_hr_loan.portal_hr_salary_tree', {'salaries': salaries})
