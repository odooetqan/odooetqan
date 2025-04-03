from odoo import http
from odoo.http import request
import base64
from datetime import datetime



# from odoo import http
# from odoo.http import request

class PortalApproval(http.Controller):
    @http.route(['/my/approval'], type='http', auth='user', website=True)
    def portal_approval_list(self, **kwargs):
        approval_requests = request.env['approval.request'].sudo().search([('request_owner_id', '=', request.env.user.id)])
        categories = request.env['approval.category'].sudo().search([])
        return request.render('portal_approval.portal_approval_list', {
            'approval_requests': approval_requests,
            'categories': categories,
        })

    @http.route(['/my/approval/new'], type='http', auth='user', website=True)
    def portal_approval_request_form(self, **kwargs):
        categories = request.env['approval.category'].sudo().search([])
        return request.render('portal_approval.portal_approval_form', {
            'categories': categories,
        })

    @http.route(['/my/approval/get_fields'], type='json', auth='user', website=True)
    def get_dynamic_fields_alias(self, category_id):
        return self.get_dynamic_fields(category_id)

# class PortalApproval(http.Controller):
    @http.route(['/my/approval/submit'], type='http', auth='user', website=True, csrf=True)
    def submit_approval_request(self, **post):
        category_id = int(post.get('category_id', 0))
        description = post.get('description')
        date = post.get('date') or False
        reference = post.get('reference') or False
        date_from = post.get('date_from') or False
        date_to = post.get('date_to') or False
        # Convert the ISO datetime (with "T") to Odoo's expected format by replacing "T" with a space.
        if date_from:
            date_from = date_from.replace('T', ' ')
        if date_to:
            date_to = date_to.replace('T', ' ')
        if date:
            date = date.replace('T', ' ')
            
        amount = float(post.get('amount', 0.0)) if post.get('amount') else 0.0
        document = post.get('document')

        uploaded_file = post.get('document')
        document = False
        if uploaded_file:
            document = base64.b64encode(uploaded_file.read()).decode('utf-8')
    
        # إنشاء الطلب
        request.env['approval.request'].sudo().create({
            'category_id': category_id,
            'name': description,
            'date': date,
            'reference': reference,
            'date_from': date_from,
            'date_to': date_to,
            'amount': amount,
            'document': document,  # <-- الآن أصبح بصيغة base64
            'request_owner_id': request.env.user.id,
        })
        return request.render('portal_approval.portal_approval_success')

class PortalApproval(http.Controller):
    @http.route(['/my/approval/get_dynamic_fields'], type='json', auth='user', website=True)
    def get_dynamic_fields(self, category_id):
        category = request.env['approval.category'].browse(int(category_id))
        req = {
            'has_date': category.has_date,
            'has_document': category.requirer_document,
            'has_amount': category.has_amount,
        }
        return {
            'success': True,
            'html': request.env.ref('portal_approval.dynamic_fields_template')._render({'req':req}),
        }
