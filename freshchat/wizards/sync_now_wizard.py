from odoo import models, fields

class FreshchatSyncNow(models.TransientModel):
    _name = 'freshchat.sync.now'
    _description = 'Manual Sync Wizard'

    def action_sync_users(self):
        self.env['freshchat.user'].sync_users_from_api()

    def action_sync_channels(self):
        self.env['freshchat.channel'].sync_channels_from_api()