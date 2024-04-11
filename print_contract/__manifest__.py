# -*- coding: utf-8 -*-

{
    "name": "Print Contract . ",
    'version': '17.0.1.0.0',
    'sequence': '-10',
    'depends': [
        'base', 'web', 'account','contacts',
    ],
    'author': 'Siralkhatim Gamal',
    'category': 'Accounting',
    'website': 'http://acpaglobal.net/',
    'support': 'seralkhatem3210@gmail.com',
    # 'images': ['static/description/assets/ghits_labtop1.jpg'],
    'price': '0',
    'license': 'OPL-1',
    'currency': 'USD',
    'summary': """ Printing student Contract from partner form views """,
    'description': """ Printing student Contract from partner form views....
    """
    ,
    'data': [
        'view/partner.xml',
        'report/base_document_layout.xml',
        'report/res_partner.xml',
        'view/res_partner_views.xml'

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'assets': {
        'web.report_assets_common': [
            'print_contract/static/css/report_style.css',
        ],
    },
}

