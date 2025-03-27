{
    'name': 'Portal Approval',
    'version': '18.0.0.0.0',
    'category': 'Human Resources',
    'author': 'Sirelkhatim',
    'depends': [],
    'depends': ['website', 'approvals', 'base', 'portal', 'hr'],
    'data': [
        'views/portal_approval.xml',
        # 'views/dynamic_fields_template.xml',
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


