from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    replace_standard_wizard = fields.Boolean(string="Replace Standard Wizard")
