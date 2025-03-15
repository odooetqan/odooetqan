# -*- coding: utf-8 -*-
{
    'name': 'Attendance Cam',
    'version': '15.0.0',
    'summary': 'Portal Face Recognition Attendance',
    'description': """
        Allow portal users to use video cam to register attendance by matching there face 
        with user profile image and git there location long and lat then save them in attendance record
    """,
    'category': 'Human Resources',
    'author': "Neoteric Hub",
    'company': 'Neoteric Hub',
    'live_test_url': '',
    'price': 29,
    'currency': 'USD',
    'website': "https://www.neoterichub.com",
    'depends': ['website', 'hr_attendance'],
    'data': [
        'views/attendance_menu_templates.xml',
        'views/hr_attendance_portal_templates.xml',
        'views/hr_attendance.xml',
        'views/hr_attendance_settings.xml',
        'views/menu.xml',
    ],
    'demo': [],

    'assets': {
        "web.assets_frontend": [
            # to add scss and js here
            "nthub_hr_cam_attendance/static/src/lib/webcam.js",
            'nthub_hr_cam_attendance/static/src/css/web_widget_image_webcam.css',
            "nthub_hr_cam_attendance/static/src/js/attendance.js",

        ],
        "web.assets_backend": [
            # to add scss and js here

        ],
    },
    'external_dependencies': {
        'python': ['opencv-python', 'face-recognition'],
    },
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
