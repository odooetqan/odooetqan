# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Promissory',
    'version': '15.0.6.8.0',
    'author': '  Alhayah Ltd',
    'depends': ['account','contacts','partner_contact_personal_information_page'],
    'description': """Manage a...""",
    'summary': 'Odoo 15  .. ..',
    'category': 'Accounting',
    'sequence': -10,
    'website': 'sirelkhatim.unaux.com',
    'license': 'LGPL-3',
    'data': [
        'report/promissory_note.xml',
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'promissory_view.xml',
        'promissory_sequence.xml',
    ],
    'installable' : True,
    'application' : True,
}
