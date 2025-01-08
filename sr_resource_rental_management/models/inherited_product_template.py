# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################
from odoo import fields, api, models


class srProductTemplate(models.Model):
    _inherit = "product.template"

    is_rental_product = fields.Boolean("Is Rental Product")
    rented_product_tmpl_id = fields.Char()
    rental_service_tmpl_ids = fields.Char()