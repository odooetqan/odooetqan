# -*- coding: utf-8 -*-


{
    'name': 'Registeration Student Base',
    'version': '17.0.1.0.0',
    'summary': """Base Module of Registeration students in school with all configuration""",
    'description': """  """,
    'sequence': -100,
    'author': 'Alhayah Ltd.',
    'website': 'http://alhayah.edu.sa',
    'support': 's.musa@alhayah.edu.sa',
    'images': ['static/description/img1.jpeg'],
    'depends': [ 'base', 'sale','contacts', 'account_accountant' ],
    'data':[
        'security/multi_company_security.xml',
        'security/ir.model.access.csv',
        'views/configuration_registeration_view.xml',
        'views/product.xml',
        'views/students.xml',
        'views/guardians.xml',
        'views/dropofoo_reasons.xml',
        'views/promissory_sequence.xml',
        'views/promissory_view.xml',
        'report/base_document_layout.xml',
        'report/contract.xml',       
        'report/promissory_note.xml',

        'views/student_student_contract_sequence.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
