# -*- coding: utf-8 -*-

{
    'name': 'Journal Sequence',
    'version': '1.1',
    'category': 'Accounting',
    'summary': 'Journal Sequence For Invoice, bill, credit, and debit notes etc',
    'description': 'This plugin makes it simple to customise and modify the invoice, bill, credit, and debit notes sequence number from the journals.',
    'sequence': '1',
    'author': 'SprintERP',
    'website': 'http://www.sprinterp.com',
    'depends': ['account'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'license': 'LGPL-3',
    'price': 12,
    'currency': 'USD',
    'installable': True,
    'application': True,
    'post_init_hook': "create_new_journal_seqs",
    'images': ['static/description/banner.gif'],
}
