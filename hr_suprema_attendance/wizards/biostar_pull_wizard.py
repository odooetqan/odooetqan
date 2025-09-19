from odoo import api, fields, models

class BiostarPullWizard(models.TransientModel):
    _name = "biostar.pull.wizard"
    _description = "Pull Events Range"

    device_id = fields.Many2one("biostar.device", required=True)
    since = fields.Datetime(required=True, default=lambda self: fields.Datetime.now())
    until = fields.Datetime(required=True, default=lambda self: fields.Datetime.now())

    def action_pull(self):
        self.ensure_one()
        return self.device_id.action_pull_events(self.since, self.until)
