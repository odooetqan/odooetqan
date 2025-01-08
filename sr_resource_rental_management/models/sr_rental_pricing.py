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


class srRentalPricing(models.Model):
    _name = "sr.rental.pricing"
    _description = "Sr Rental Pricing"

    product_tmpl_id = fields.Many2one("product.template", string="Product Template")
    product_ids = fields.Many2many("product.product", string="Variants")
    duration = fields.Integer("Duration")
    unit = fields.Selection(
        [('hour', 'Hours'), ('day', 'Days'), ('week', 'Weeks'), ('month', 'Months')],
        "Unit",
    )
    lot_ids = fields.Many2many("stock.production.lot", string="Serial Number")
    price = fields.Float("Price")
    currency_id = fields.Many2one(
        "res.currency",
        "Currency Id",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
