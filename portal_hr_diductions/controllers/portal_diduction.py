

from odoo import http
from odoo.http import request


class PortalDiscount(http.Controller):

    @http.route(['/my/diductions'], type='http', auth='user', website=True)
    def portal_my_diductions(self, **kwargs):
        employee = request.env.user.employee_id
        diductions = request.env['hr.diduction'].sudo().search([('employee_id', '=', employee.id)])

        return request.render('portal_hr_diductions.portal_my_diductions', {
            'diductions': diductions
        })

    # @http.route(['/my/diduction/new'], type='http', auth='user', website=True)
    # def portal_diduction_request_form(self, **kwargs):
    #     categories = request.env['diduction.category'].sudo().search([])
    #     return request.render('portal_diduction.portal_diduction_form', {
    #         'categories': categories,
    #     })

# # class PortalDiduction(http.Controller):
#     @http.route(['/my/diduction/submit'], type='http', auth='user', website=True, csrf=True)
#     def submit_diduction_request(self, **post):
#         category_id = int(post.get('category_id', 0))
#         description = post.get('description')
#         date_from = post.get('date_from') or False
#         date_to = post.get('date_to') or False

#         # Convert the ISO datetime (with "T") to Odoo's expected format by replacing "T" with a space.
#         if date_from:
#             date_from = date_from.replace('T', ' ')
#         if date_to:
#             date_to = date_to.replace('T', ' ')

#         amount = float(post.get('amount', 0.0)) if post.get('amount') else 0.0
#         document = post.get('document')

#         # إنشاء الطلب
#         request.env['diduction.request'].sudo().create({
#             'category_id': category_id,
#             'name': description,
#             'date_from': date_from,
#             'date_to': date_to,
#             'amount': amount,
#             'document': document,
#             'request_owner_id': request.env.user.id,
#         })
#         return request.render('portal_diduction.portal_diduction_success')

#         # return request.render('portal_diduction_success', {})
