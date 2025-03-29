{
    'name': 'Portal HR Attendance',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Portal page for employees to Check In/Check Out',
    'author': 'Sirelkhatim',
    'depends': [
        'base',
        'hr_attendance',  # Attendance module
        'portal',  # Portal module to access the user portal
        'website',  # Required for frontend assets and views
        'web',  # ✅ Add this to ensure JS dependencies

    ],
    'data': [
        'views/portal_attendance_templates.xml',  # QWeb Templates for the portal
    ],
    # 'assets': {
    #     'web.assets_frontend': [
    #         '/portal_hr_attendance/static/src/js/attendance_toggle.js',
    #     ],
    # },


    'assets': {
        'web.assets_frontend': [
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
