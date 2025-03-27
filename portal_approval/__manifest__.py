{
    'name': 'Portal Approval',
    'version': '18.0.0.0.0',
    'depends': ['base', 'portal', 'hr', 'hr_holidays', 'portal_attendance_artx', 'ent_ohrms_loan'],
    'data': [
        'views/portal_approval.xml',
        'views/dynamic_fields_template.xml',
        'security/security.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_attendance_artx/static/src/js/portal_approval.js',
        ],
    },
    # 'data': [
    #     'security/ir.model.access.csv',
    #     'security/hr_loan_security.xml',
    #     'views/hr_loan_portal_templates.xml',
    # ],
}


