# -*- coding: utf-8 -*-
{
    'name': 'Print Contract . ',
    'version': '17.0.1.0.0',
    'sequence': '-10',
    'depends': [
        'base', 'web', 'account','contacts',
    ],
    'author': 'Siralkhatim Gamal',
    'category': 'Accounting',
    'website': 'http://acpaglobal.net/',
    'support': 'seralkhatem3210@gmail.com',


    'data': [
        'view/partner.xml',
        'report/base_document_layout.xml',
        'report/res_partner.xml',
        # 'view/res_partner_views.xml'

    ],
   
    'summary': """Base Module of Registeration students in school with all configuration""",
    'description': """
    """,
    'sequence': -100,

    'images': ['static/description/img1.jpeg'],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:



# # -*- coding: utf-8 -*-

# {
#     'name': 'Print Contract . ',
#     'version': '17.0.1.0.0',
#     'sequence': '-10',
#     'depends': [
#         'base', 'web', 'account','contacts',
#     ],
#     'author': 'Siralkhatim Gamal',
#     'category': 'Accounting',
#     'website': 'http://acpaglobal.net/',
#     'support': 'seralkhatem3210@gmail.com',
#     # 'images': ['static/description/assets/ghits_labtop1.jpg'],
#     'price': '0',
#     'license': 'OPL-1',
#     'currency': 'USD',
#     'summary': """ Printing student Contract from partner form views """,
#     'description': """ Printing student Contract from partner form views....
#     """
#     ,
#     'data': [
#         'view/partner.xml',
#         'report/base_document_layout.xml',
#         'report/res_partner.xml',
#         # 'view/res_partner_views.xml'

#     ],
#     'installable': True,
#     'auto_install': False,
#     'application': True,
#     # 'assets': {
#     #     'web.report_assets_common': [
#     #         'print_contract/static/css/report_style.css',
#     #     ],
#     # },
# }





# # -*- coding: utf-8 -*-

# {
#     "name": "Print Contract . ",
#     'version': '17.0.1.0.0',
#     'sequence': '-10',
#     'depends': [
#         'base', 'web', 'account','contacts',
#     ],
#     'author': 'Siralkhatim Gamal',
#     'category': 'Accounting',
#     'website': 'http://acpaglobal.net/',
#     'support': 'seralkhatem3210@gmail.com',
#     # 'images': ['static/description/assets/ghits_labtop1.jpg'],
#     'price': '0',
#     'license': 'OPL-1',
#     'currency': 'USD',
#     'summary': """ Printing student Contract from partner form views """,
#     'description': """ Printing student Contract from partner form views....
#     """
#     ,
#     'data': [
#         'view/partner.xml',
#         'report/base_document_layout.xml',
#         'report/res_partner.xml',
#         'view/res_partner_views.xml'

#     ],
#     'installable': True,
#     'auto_install': False,
#     'application': True,

#     'assets': {
#         'web.assets_common': [
#                         'print_contract/static/css/report_style.css',
#         ],
#     },
#     # 'assets': {
#     #     'web.report_assets_common': [
#     #         'print_contract/static/css/report_style.css',
#     #     ],
#     # },
# }