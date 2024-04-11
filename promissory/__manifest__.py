# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.

###############################################################################
{
    'name': 'السندات لأمر شركة الحياة',
    'version': '17.0.1.0.0',
    'author': 'شركة الحياة المحدودة',    
    'category': 'Accounting',
    'sequence': -105,
    'summary': "Module for e-Invoicing For Saudi | Saudi VAT Invoice | Saudi "
               "Electronic Invoice | Saudi Zatca",
    'description': "e-Invoicing For Saudi,Saudi VAT Invoice,Saudi Electronic "
                   "Invoice,Saudi Zatca,Zatca,Saudi,e-Invoicing",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account','contacts','partner_contact_personal_information_page'],    
    'data': [
        # 'data/account_asset_data.xml',
        'report/promissory_note.xml',
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'promissory_view.xml',
        'promissory_sequence.xml',
        
    ],

    
    # 'data': [
    #     'views/res_config_settings_views.xml',
    #     'views/account_move_views.xml',
    #     'report/account_move_reports.xml',
    #     'report/vat_invoice_report_templates.xml',
    #     'report/simplified_tax_report_templates.xml'
    # ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}



# {
#     'name': 'السندات لأمر شركة الحياة',
#     'version': '17.0.1.0.0',
#     'author': 'شركة الحياة المحدودة',
#     'depends': ['account','contacts','partner_contact_personal_information_page'],
#     'description': """Manage a...""",
#     'summary': 'Odoo 15  .. ..',
#     'category': 'Accounting',
#     'sequence': -10,
#     'website': 'sirelkhatim.unaux.com',
#     'license': 'LGPL-3',
#     # 'images': ['static/description/assets.gif'],
#     'data': [
#         # 'data/account_asset_data.xml',
#         'report/promissory_note.xml',
#         'security/account_asset_security.xml',
#         'security/ir.model.access.csv',
#         'promissory_view.xml',
#         'promissory_sequence.xml',
        
#     ],
#     # 'assets': {
#     #     'web.assets_backend': [
#     #         'om_account_asset/static/src/scss/account_asset.scss',
#     #         'om_account_asset/static/src/js/account_asset.js',
#     #     ],
#     #     'web.qunit_suite_tests': [
#     #         ('after', 'web/static/tests/legacy/views/kanban_tests.js', '/om_account_asset/static/tests/account_asset_tests.js'),
#     #     ],
#     # },
#     'installable' : True,
#     'application' : True,
# }
