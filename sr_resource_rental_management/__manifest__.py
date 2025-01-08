# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

{
    "name": "Resource Rental Management",
    "version": "15.0.0.0",
    'category': 'Sales/Sales',
    "license": "OPL-1",
    "summary": "Resource rental management resources like products equipment machinery cars rental management system hire equipment for rent hire cars on rent complete work cycle for rental management system in odoo",
    "description": """
    Tags:
        odoo rental management system, Hire equipment on rent, Hire Vehical on rent, hire car on rent, 
        hire machinery on rent , resources on rent, fleet on rent,
        machine rental management, equipment rental management
    with the help of this odoo module you can rent anything.
    resource rental management system
    products rental management system
    machinery rental management system
    cars rental management system
    fleet rental management system
    hire fleet on rent
    hire cars on rent
    hire machinery on rent
    hire resources on rent
    Sitaram Solutions developed new odoo application that will help you to rent resources, products, equipment, machinery, car, house, anything can be rented.
    pickup rental orders
    return rental orders
    pickup order from nearest shop
    maintain with serial numbers for products
    resources pick up with serial numbers
    resources return with serial numbers
    track pickup and return rental orders
    email remainder for pick up rental order
    email remainder for return rental order
    email remainder for pick up equipment for rent
    email remainder for pick up resources for rent
    email remainder for pick up machinery for rent
    filter by pick up rental order
    filter by return rental order
    manage rental orders
    reserve your products
    reserve your resources
    reserve your equipment
    reserve your machinery
    reserve your rental order
    """,
    "price": 45,
    "currency": 'EUR',
    'author': 'Sitaram',
    'depends': ['base', 'sale', 'stock'],
    "data": [
        "data/rental_order_sequence_data.xml",
        "data/cron_data.xml",
        "data/mail_data.xml",
        "security/ir.model.access.csv",
        "views/sr_rental_view.xml",
        "views/inherited_res_config_settings_view.xml",
        "views/inherited_product_template_view.xml",
        "views/inherited_sale_order_view.xml",
        "wizard/sr_product_rent_wizard_view.xml",
        "wizard/sr_rental_order_wizard_view.xml",
        "report/rental_report_view.xml",
        "report/report_pickup_template.xml",
        "report/report_return_template.xml",
    ],
    "demo": [],
    "qweb": ["static/src/xml/datepicker_widget.xml"],
    'website':'https://www.sitaramsolutions.in',
    'application': True,
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/Gd1t4H97Qbg',
    "images":['static/description/banner.png'],
}
