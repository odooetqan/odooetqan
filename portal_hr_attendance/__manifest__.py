{
    'name': 'Portal HR Attendance',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Portal page for employees to Check In/Check Out',
    'author': 'Sirelkhatim',
    'depends': [
        'base',
        'hr_attendance',
        'portal',
        'website',
        'web',  # Ensure the 'web' module is included
    ],
    'data': [
        'views/portal_attendance_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Ensure Odoo core dependencies are loaded first
            'web/static/src/js/public/public_widget.js',
            'web/static/src/js/core/ajax.js',

            # Your custom JS and CSS
            'portal_hr_attendance/static/src/js/attendance_toggle.js',
            'portal_hr_attendance/static/src/css/attendance_styles.css',
        ],
        'web.assets_qweb': [
            'portal_hr_attendance/static/src/xml/portal_hr_attendance_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
}