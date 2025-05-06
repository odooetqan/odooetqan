{
    'name': 'Payslip Excel Export',
    'version': '1.0',
    'category': 'Payroll',
    'depends': ['hr_payroll'],
    'data': [
        'views/payslip_export_wizard_view.xml',
        'views/payslip_action.xml',
    ],
    'installable': True,
    'auto_install': False,
}
