# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

PARAM_PREFIX = "zk_attendance_push_sh."

class ZKAttendanceConfig(models.TransientModel):
    _name = "zk.attendance.config"
    _description = "ZK Attendance Push Configuration"

    zk_local_url = fields.Char(string="Local Odoo URL")
    zk_local_db = fields.Char(string="Local DB Name")
    zk_local_user = fields.Char(string="Local Username")
    zk_local_password = fields.Char(string="Local Password")

    zk_sh_url = fields.Char(string="Odoo.sh URL")
    zk_sh_db = fields.Char(string="Odoo.sh DB Name")
    zk_sh_user = fields.Char(string="Odoo.sh Username")
    zk_sh_password = fields.Char(string="Odoo.sh Password")

    zk_days_back_default = fields.Integer(string="Default Days Back", default=2)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ICP = self.env["ir.config_parameter"].sudo()
        getp = ICP.get_param
        res.update(
            zk_local_url=getp(PARAM_PREFIX+"local_url", ""),
            zk_local_db=getp(PARAM_PREFIX+"local_db", ""),
            zk_local_user=getp(PARAM_PREFIX+"local_user", ""),
            zk_local_password=getp(PARAM_PREFIX+"local_password", ""),
            zk_sh_url=getp(PARAM_PREFIX+"sh_url", ""),
            zk_sh_db=getp(PARAM_PREFIX+"sh_db", ""),
            zk_sh_user=getp(PARAM_PREFIX+"sh_user", ""),
            zk_sh_password=getp(PARAM_PREFIX+"sh_password", ""),
            zk_days_back_default=int(getp(PARAM_PREFIX+"days_back_default", "2") or 2),
        )
        return res

    def action_save(self):
        self.ensure_one()
        ICP = self.env["ir.config_parameter"].sudo()
        setp = ICP.set_param
        setp(PARAM_PREFIX+"local_url", self.zk_local_url or "")
        setp(PARAM_PREFIX+"local_db", self.zk_local_db or "")
        setp(PARAM_PREFIX+"local_user", self.zk_local_user or "")
        setp(PARAM_PREFIX+"local_password", self.zk_local_password or "")
        setp(PARAM_PREFIX+"sh_url", self.zk_sh_url or "")
        setp(PARAM_PREFIX+"sh_db", self.zk_sh_db or "")
        setp(PARAM_PREFIX+"sh_user", self.zk_sh_user or "")
        setp(PARAM_PREFIX+"sh_password", self.zk_sh_password or "")
        setp(PARAM_PREFIX+"days_back_default", str(self.zk_days_back_default or 2))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("Saved"), "message": _("Configuration saved successfully."), "sticky": False},
        }
