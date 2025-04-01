{
    'name': 'Portal Approval',
    'version': '18.0.0.0.0',
    'category': 'Human Resources',
    'author': 'Sirelkhatim',
    'depends': ['website', 'approvals', 'base', 'portal', 'hr'],
    'data': [
        'views/portal_approval.xml',
        'views/dynamic_fields_template.xml',
        'security/security.xml',
    ],
    'assets': {
        'web.assets_frontend':
        [
            'portal_approval/static/src/js/portal_approval.esm.js',
            'portal_approval/static/src/css/style.css',
        ],
    },
}


