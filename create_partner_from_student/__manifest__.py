# -*- coding: utf-8 -*-


{
    'name': 'Create Partner From Students',
    'version': '17.0.1.0.0',
    'summary': """ This module helps you to create partner from student""",
    'description': """This module helps you to create partner from student """,
    'sequence': -100,
    'author': 'Alhayah Ltd.',
    'website': 'http://alhayah.edu.sa',
    'support': 's.musa@alhayah.edu.sa',
    # 'images': ['static/description/img1.jpeg'],
    'depends': [ 'base', 'sale','contacts', 'school_reg_base'], #, 'account_analytic_distribution' ],
    'data':[
        'views/create_partner_from_student.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
