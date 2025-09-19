# -*- coding: utf-8 -*-
################################################################################
#    Sirelkhatim Technologies
#    License: LGPL-3
################################################################################
{
    "name": "BioStar Attendance Connector (Suprema)",
    "summary": "Sync Suprema BioStar 2 attendance logs into Odoo HR Attendance with multi-device support, wizards, and scheduled jobs.",
    "version": "17.0.1.0.0",
    "category": "Human Resources/Attendance",
    "author": "Sirelkhatim Gamal",
    "website": "https://sirelkhatim.uk",
    "license": "LGPL-3",

    "depends": ["base", "mail", "hr", "hr_attendance"],

    "data": [
        "security/ir.model.access.csv",
        "views/biostar_device_views.xml",
        "views/biostar_user_views.xml",
        "views/biostar_wizards.xml",
        "views/biostar_attendance_log_views.xml",
        "views/biostar_menus.xml",
        "data/biostar_cron.xml",
    ],

    "assets": {
        "web.assets_backend": [
            # Keep if you add any backend JS/CSS under static/src
            "hr_suprema_attendance/static/src/**/*",
        ],
    },

    "images": [
        "static/description/banner.png",
        "static/description/icon.png",
        "static/description/screens/device_form.png",
        "static/description/screens/user_map.png",
        "static/description/screens/wizard_sync.png",
        "static/description/screens/logs_tree.png",
    ],

    "external_dependencies": {
        "python": ["requests"],
    },

    "application": True,
    "installable": True,

    "description": """
BioStar Attendance Connector (Suprema)
======================================

Bring Suprema BioStar 2 attendance into Odoo HR smoothly and reliably.

Key Features
------------
- Multi-device support (multiple BioStar servers or sites)
- Secure API connection with connectivity test & error logging
- One-click manual sync wizard + scheduled (cron) automatic sync
- Intelligent de-duplication of logs and configurable timezone handling
- Flexible employee mapping by device user ID / employee field
- Mail notifications for failures and activity tracking on records

What's Inside (Technical)
-------------------------
- Models:
  * biostar.device — connection profiles (URL, credentials, timezone, status)
  * biostar.user — mapping BioStar user ↔ Odoo employee
  * biostar.attendance.log — raw log store (before HR Attendance creation)
- Wizards:
  * biostar.sync.wizard — range-based pull, dry-run, and report summary
- Scheduled Jobs:
  * biostar_attendance_sync — periodic sync from BioStar 2

Compatibility
-------------
- ✅ Odoo 17 Community & Enterprise
- ✅ Tested with BioStar 2 REST endpoints

Support
-------
Need help or customization? Reach out via https://sirelkhatim.uk
(Arabic/English support available).

العربية (ملخص)
--------------
- مزامنة سجلات بصمة/وجه BioStar 2 تلقائياً إلى حضور الموظفين في أودو
- دعم أجهزة متعددة، مع نافذة مزامنة يدوية + مجدول تلقائي
- معالجة المناطق الزمنية، منع التكرار، وإشعارات بريدية عند الأخطاء
- خرائط مرنة بين مستخدم الجهاز وموظف أودو
""",
}
