# -*- coding: utf-8 -*-
{
    'name': 'Attendance',
    'version': '16.0.1',
    'category': 'Human Resources/Employees',
    'sequence': 1,
    'summary': """
    Attendance with Geolocation through V3C Android Mobile Application.
    """,
    'author': 'V3CodeStudio',
    "price": 99.00,
    "currency": "USD",
    'website': '',
    "images": ["static/description/banner.png"],
    'depends': [
        'sale_management',
        'hr_attendance'],
    'data': [
        'views/hr_attendance_views.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
