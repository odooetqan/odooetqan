# -*- coding: utf-8 -*-
{
    'name': "Check in-Out Restriction for Attendance Location",

    'summary': "Track attendance based on the office location and specified distance allowance, and prevent users from checking in or out if they are outside the designated range.",

    'description': """
        This module calculates attendance based on the office location and allowed distance. 
        It checks whether the employee's check-in location is within the allowed range of the office location.
    """,

    'author': "Aptuem Solutions",
    'website': "https://www.aptuem.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Attendance',
    'version': '0.1',
    'module_type': 'official',
    'license': 'AGPL-3',
    'images': ['static/description/thumbnail.gif'],

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance'],

    # always loaded
    'data': [
        # 'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
