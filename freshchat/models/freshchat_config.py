from odoo import models, fields

class FreshchatConfig(models.Model):
    _name = 'freshchat.config'
    _description = 'Freshchat Configuration'
    _rec_name = 'account_url'

    account_url = fields.Char(required=True, help="e.g., https://yourcompany.freshchat.com")
    api_token = fields.Char(required=True, help="Bearer Token from Freshchat")
    is_active = fields.Boolean(default=True)