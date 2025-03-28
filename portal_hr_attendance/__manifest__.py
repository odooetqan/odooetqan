{
    'name': 'Portal HR Attendance',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Portal page for employees to Check In/Check Out',
    'auther': 'Srelkhatim',
    'depends': ['base', 'hr_attendance', 'portal'],  # Make sure hr_attendance & portal are included
    'data': [
        'views/portal_attendance_templates.xml',  # We'll define the QWeb templates here
    ],
    'installable': True,
    'application': False,
}
