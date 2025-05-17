from odoo import http
from odoo.http import request
import json

class FreshchatController(http.Controller):

    @http.route('/freshchat/sync_users', type='json', auth='user')
    def sync_users(self):
        return request.env['freshchat.user'].sudo().sync_users_from_api()