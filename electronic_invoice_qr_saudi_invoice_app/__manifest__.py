# -*- coding: utf-8 -*-
{
    'name': 'Electronic KSA Invoice - Invoice, Credit Note, Bill, Refund KSA Report',
    "author": "Edge Technologies",
    'version': '17.0.1.0',
    'description': """ 
        QR Code Invoice
    """,
    "license" : "OPL-1",
    "sequence":-100,	
    'depends': ['base','account','portal','web'],
    "summary" : 'KSA electronic invoice for KSA saudi electronic invoice for saudi invoice saudi QR code invoice QR code invoice for KSA saudi electronic invoice electronic QR invoice QR code on invoice saudi einvoice KSA e-invoice saudi e-invoice KSA invoicing for KSA',
    'live_test_url': "https://youtu.be/MYUkIY2PRmg",
    "images":["static/description/main_screenshot.png"],
    'data': [
	        "report/account_invoice_report_template.xml",
            "views/qr_code_invoice_view.xml",
            ],
    'installable': True,
    'auto_install': False,
    'price': 15,
    'currency': "EUR",
    'category' : 'Accounting'
}
