from odoo import http
from odoo.http import request


class PortalApproval(http.Controller):
    @http.route(['/my/approval/submit'], type='http', auth='user', website=True, csrf=True)
    def submit_approval_request(self, **post):
        category_id = int(post.get('category_id', 0))
        description = post.get('description')
        date_from = post.get('date_from') or False
        date_to = post.get('date_to') or False
        amount = float(post.get('amount', 0.0)) if post.get('amount') else 0.0
        document = post.get('document')

        # إنشاء الطلب
        request.env['approval.request'].sudo().create({
            'category_id': category_id,
            'name': description,
            'date_from': date_from,
            'date_to': date_to,
            'amount': amount,
            'document': document,
            'request_owner_id': request.env.user.id,
        })

        return request.render('portal_approval_success', {})


    @http.route(['/my/approval'], type='http', auth="user", website=True)
    def portal_approval(self, **kwargs):
        categories = request.env['approval.category'].sudo().search([])
        return request.render('portal_approval.portal_approval_form', {
            'categories': categories,
        })

    # @http.route(['/my/approval/submit'], type='http', auth="user", website=True, methods=['POST'])
    # def portal_approval_submit(self, **post):
    #     category_id = int(post.get('category_id'))
    #     description = post.get('description')
    #     date_from = post.get('date_from')
    #     date_to = post.get('date_to')
    #     document = post.get('document')
    #     amount = post.get('amount')

    #     # Create approval request
    #     request.env['approval.request'].sudo().create({
    #         'category_id': category_id,
    #         'request_owner_id': request.env.user.id,
    #         'description': description,
    #         'date_start': date_from,
    #         'date_end': date_to,
    #         'attachment_ids': [(0, 0, {
    #             'name': document.filename,
    #             'datas': document.read().encode('base64'),
    #             'res_model': 'approval.request',
    #         })] if document else False,
    #         'amount': amount,
    #     })
    #     return request.redirect('/my/approval')


# class ProtalDynamicFieldTemplate(http.Controller):

#     @http.route(['/my/approval/get_fields'], type='json', auth="user")
#     def get_dynamic_fields(self, category_id):
#         category = request.env['approval.category'].sudo().browse(int(category_id))
#         values = {
#             'has_date': category.has_date,
#             'has_document': category.requirer_document,
#             'has_amount': category.has_amount,
#         }
#         return request.env.ref('portal_approval.dynamic_fields_template').render(values)

class PortalApproval(http.Controller):
    @http.route(['/my/approval/get_dynamic_fields'], type='json', auth='user', website=True)
    def get_dynamic_fields(self, category_id):
        category = request.env['approval.category'].browse(int(category_id))
        values = {
            'has_date': category.has_date,
            'has_document': category.requirer_document,
            'has_amount': category.has_amount,
        }
        return {
            'success': True,
            'html': request.env.ref('portal_approval.dynamic_fields_template')._render(values),
        }
