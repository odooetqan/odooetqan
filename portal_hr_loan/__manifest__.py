{
    'name': 'Portal HR Loan',
    'version': '1.0',
    'depends': ['base', 'portal', 'hr', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_loan_security.xml',
        'views/hr_loan_portal_templates.xml',
    ],
}
