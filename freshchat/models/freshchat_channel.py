from odoo import models, fields

class FreshchatChannel(models.Model):
    _name = 'freshchat.channel'
    _description = 'Freshchat Channel'

    name = fields.Char(required=True)
    external_id = fields.Char(string="External ID", required=True, index=True)
    enabled = fields.Boolean()
    public = fields.Boolean()
    tag_ids = fields.Many2many('res.partner.category', string="Tags")