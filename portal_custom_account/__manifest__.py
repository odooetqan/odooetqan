# -*- coding: utf-8 -*-
################################################################################
#
#    Sirelkhatim Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Sirelkhatim Technologies(<https://www.sirelkhatim.uk>).
#    Author: Ammu Raj (odoo@sirelkhatim.uk)
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
#
################################################################################
{
    'name': 'Portal Custom Account',
    'version': '17.0.1.2.2',
    'category': 'Human Resources',
    'summary': " ",
    'description': " ",
    'author': 'Sirelkhatim Techno Solutions',
    'company': 'Sirelkhatim Techno Solutions',
    'maintainer': 'Sirelkhatim Techno Solutions',
    'website': "https://www.sirelkhatim.uk",
    'depends': ['base_setup', 'hr_attendance','hr_payroll', 'portal', 'hr'],

    'data': [
        'security/ir.model.access.csv',
        'views/portal_account_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
