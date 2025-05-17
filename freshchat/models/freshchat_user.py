from odoo import models, fields

class FreshchatUser(models.Model):
    _name = 'freshchat.user'
    _description = 'Freshchat User'

    name = fields.Char()
    email = fields.Char()
    phone = fields.Char()
    external_id = fields.Char(string="External ID", required=True, index=True)
    partner_id = fields.Many2one('res.partner', string="Linked Partner")