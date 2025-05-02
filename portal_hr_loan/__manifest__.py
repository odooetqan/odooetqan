{
    'name': 'Portal HR Loan',
    'version': '17.0.0.0.0',
    'depends': ['base', 'portal', 'hr', 'hr_holidays', 'portal_attendance_artx_update', 'ent_ohrms_loan'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_loan_security.xml',
        'views/hr_loan_portal_templates.xml',
    ],
}
