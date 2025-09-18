{
    "name": "BioStar Attendance Connector",
    "version": "17.0.1.0.0",
    "author": "Sirelkhatim Gamal",
    "depends": ["hr", "hr_attendance", "base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/biostar_device_views.xml",
        "views/biostar_user_views.xml",
        "views/biostar_wizards.xml",
        "data/biostar_cron.xml",
        "views/biostar_menus.xml",
        "views/biostar_attendance_log_views.xml",
    ],
    "installable": True,
}
