# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'E-Invoicing For Saudi | Saudi VAT Invoice '
            '| Saudi Electronic Invoice | Saudi Zatca',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': "This module enables VAT-compliant e-Invoicing for Saudi Arabia,"
               " following ZATCA (Fatoorah) regulations. It supports generating"
               " electronic invoices with QR codes and structured formats for "
               "both simplified and standard invoices",
    'description': "e-Invoicing For Saudi,Saudi VAT Invoice,Saudi Electronic "
                   "Invoice,Saudi Zatca,Zatca,Saudi,e-Invoicing",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account', 'account_payment'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'report/account_move_reports.xml',
        'report/vat_invoice_report_templates.xml',
        'report/simplified_tax_report_templates.xml'
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
