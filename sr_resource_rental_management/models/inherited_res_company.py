# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sr_rental_loc_id = fields.Many2one(
        "stock.location",
        string="In rent",
        domain=[('usage', '=', 'internal')],
        help=(
            "This technical location serves as stock for products currently in rental"
            "This location is internal because products in rental"
            "are still considered as company assets."
        ),
    )

    def _create_rental_location(self):
        for company in self:
            if not company.sr_rental_loc_id:
                company.sr_rental_loc_id = (
                    self.env['stock.location']
                    .sudo()
                    .create(
                        {
                            "name": "Rental",
                            "usage": "internal",
                            "company_id": company.id,
                        }
                    )
                )
