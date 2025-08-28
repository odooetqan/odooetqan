# -*- coding: utf-8 -*-
{
    "name": "ZK Attendance Push to Odoo.sh",
    "version": "17.0.1.0.0",
    "summary": "Push zk.machine.attendance from a local Odoo to Odoo.sh via XML-RPC (manual & scheduled).",
    "category": "Human Resources/Attendance",
    "depends": ["base", "hr"],
    "data": [
        "security/ir.model.access.csv",
        # "views/res_config_settings_views.xml",
        "views/zk_push_views.xml",
        "data/ir_cron.xml",
        "views/zk_config_views.xml"
        ],
    "license": "OPL-1",
    "application": False,
    "installable": True
}
