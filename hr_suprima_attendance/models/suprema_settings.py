from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SupremaSettings(models.TransientModel):
    _inherit = "res.config.settings"

    suprema_base_url = fields.Char(string="BioStar 2 Base URL", help="e.g. https://10.4.30.7")
    suprema_username = fields.Char(string="BioStar 2 Username")
    suprema_password = fields.Char(string="BioStar 2 Password")
    suprema_verify_ssl = fields.Boolean(string="Verify SSL Certificate", default=False)
    suprema_user_field = fields.Selection([
        ("barcode", "Employee Badge/Barcode"),
        ("work_email", "Employee Work Email"),
        ("x_suprema_user_id", "Custom Field: x_suprema_user_id"),
    ], default="barcode", string="Match BioStar User To Employee By")

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        res.update(
            suprema_base_url=ICP.get_param("suprema.base_url", default=""),
            suprema_username=ICP.get_param("suprema.username", default=""),
            suprema_password=ICP.get_param("suprema.password", default=""),
            suprema_verify_ssl=ICP.get_param("suprema.verify_ssl", default="0") == "1",
            suprema_user_field=ICP.get_param("suprema.user_field", default="barcode"),
        )
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("suprema.base_url", self.suprema_base_url or "")
        ICP.set_param("suprema.username", self.suprema_username or "")
        ICP.set_param("suprema.password", self.suprema_password or "")
        ICP.set_param("suprema.verify_ssl", "1" if self.suprema_verify_ssl else "0")
        ICP.set_param("suprema.user_field", self.suprema_user_field or "barcode")
