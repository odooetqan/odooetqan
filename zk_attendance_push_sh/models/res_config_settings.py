# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    zk_local_url = fields.Char(string="Local Odoo URL")
    zk_local_db = fields.Char(string="Local DB Name")
    zk_local_user = fields.Char(string="Local Username")
    zk_local_password = fields.Char(string="Local Password")

    zk_sh_url = fields.Char(string="Odoo.sh URL")
    zk_sh_db = fields.Char(string="Odoo.sh DB Name")
    zk_sh_user = fields.Char(string="Odoo.sh Username")
    zk_sh_password = fields.Char(string="Odoo.sh Password")

    zk_days_back_default = fields.Integer(string="Default Days Back", default=2)

    def set_values(self):
        res = super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param("zk_attendance_push_sh.local_url", self.zk_local_url or "")
        ICP.set_param("zk_attendance_push_sh.local_db", self.zk_local_db or "")
        ICP.set_param("zk_attendance_push_sh.local_user", self.zk_local_user or "")
        ICP.set_param("zk_attendance_push_sh.local_password", self.zk_local_password or "")
        ICP.set_param("zk_attendance_push_sh.sh_url", self.zk_sh_url or "")
        ICP.set_param("zk_attendance_push_sh.sh_db", self.zk_sh_db or "")
        ICP.set_param("zk_attendance_push_sh.sh_user", self.zk_sh_user or "")
        ICP.set_param("zk_attendance_push_sh.sh_password", self.zk_sh_password or "")
        ICP.set_param("zk_attendance_push_sh.days_back_default", str(self.zk_days_back_default or 2))
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            zk_local_url=ICP.get_param("zk_attendance_push_sh.local_url", ""),
            zk_local_db=ICP.get_param("zk_attendance_push_sh.local_db", ""),
            zk_local_user=ICP.get_param("zk_attendance_push_sh.local_user", ""),
            zk_local_password=ICP.get_param("zk_attendance_push_sh.local_password", ""),
            zk_sh_url=ICP.get_param("zk_attendance_push_sh.sh_url", ""),
            zk_sh_db=ICP.get_param("zk_attendance_push_sh.sh_db", ""),
            zk_sh_user=ICP.get_param("zk_attendance_push_sh.sh_user", ""),
            zk_sh_password=ICP.get_param("zk_attendance_push_sh.sh_password", ""),
            zk_days_back_default=int(ICP.get_param("zk_attendance_push_sh.days_back_default", "2") or 2),
        )
        return res
