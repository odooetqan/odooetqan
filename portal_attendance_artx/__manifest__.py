{
    'name': 'Employee Portal Attendance Management',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Allows HR managers or administrators to automatically create portal users for employees and manage attendance via the portal.',
    'description': """This module extends the HR and Portal functionalities in Odoo by allowing HR managers and super administrators to easily create portal users for employees.
        Key Features:
        - A button on the employee form to create a portal user automatically.
        - Portal users are assigned the "Portal" access rights and linked to their employee records.
        - Portal users can log in to the Odoo portal and check-in/check-out attendance from the portal web interface.
        - Automatically manage the linking of employees to the portal user accounts.        
    """,
    'author': "Areterix Technologies",
    'price': '10.0',
    'currency': 'USD',
    'website': 'https://areterix.com',
    'depends': ['hr_attendance', 'portal', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/attendance_views.xml',
        'views/hr_attendance_correction_views.xml',    
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_attendance_artx/static/src/js/attendance.js',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
}
