from odoo import http
from odoo.http import request

class PortalAccount(http.Controller):

    @http.route(['/my/account'], type='http', auth="user", website=True)
    def portal_my_account(self, **kwargs):
        """ Render the custom portal account page """
        user = request.env.user
        employee = user.employee_id  # Fetch employee linked to user

        values = {
            'user': user,
            'employee': employee,
        }

        return request.render('portal_custom_account.portal_account_template', values)
