# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'السندات لأمر شركة الحياة',
    'version': '17.0.1.0.0',
    'author': 'شركة الحياة المحدودة',
    'depends': ['account','contacts','partner_contact_personal_information_page'],
    'description': """Manage a...""",
    'summary': """Odoo 15  .. ..""",
    'category': 'Accounting',
    'sequence': -10,
    'website': 'sirelkhatim.unaux.com',
    'license': 'LGPL-3',
    # 'images': ['static/description/assets.gif'],
    'data': [
        # 'data/account_asset_data.xml',
        'report/promissory_note.xml',
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'promissory_view.xml',
        'promissory_sequence.xml',
        
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'om_account_asset/static/src/scss/account_asset.scss',
    #         'om_account_asset/static/src/js/account_asset.js',
    #     ],
    #     'web.qunit_suite_tests': [
    #         ('after', 'web/static/tests/legacy/views/kanban_tests.js', '/om_account_asset/static/tests/account_asset_tests.js'),
    #     ],
    # },
    'installable' : True,
    'application' : True,
}
