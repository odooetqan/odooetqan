# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################
import calendar
from odoo import fields, api, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class srProductRentWizard(models.TransientModel):
    _name = "sr.rental.product.wizard"
    _description = "Sr Rental Product Wizard"

    sale_order_id = fields.Many2one("sale.order", string="Sale Id")
    product_id = fields.Many2one("product.product", string="Product")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    pickup_date = fields.Date(string="Pickup Date")
    return_date = fields.Date(string="Return Date")
    quantity = fields.Integer(string="Quantity", default=1.00)
    unit_price = fields.Float(string="Unit Price")

    @api.constrains('pickup_date', 'return_date')
    def validate_date(self):
        if (
            self.return_date
            and self.pickup_date
            and self.return_date < self.pickup_date
        ):
            raise ValidationError(_("Please select pickup date before return date."))

    @api.onchange("pickup_date", "return_date", "product_id", "quantity")
    def onchange_quantity(self):
        if self.pickup_date and self.return_date:
            days = abs((self.pickup_date - self.return_date).days)
            day_price = self.product_id.list_price * days
            self.unit_price = self.quantity * day_price
        else:
            self.unit_price = self.quantity * self.product_id.list_price

    def add_rental_product_line(self):
        product_name = ""
        for val in self.product_id.name_get():
            product_name = val[1]
        is_edit_rental_line = self._context.get('is_edit_rental_line')
        if not is_edit_rental_line:
            vals = {
                "product_id": self.product_id.id,
                "name": "%s\n%s to %s"
                % (product_name, self.pickup_date, self.return_date),
                "product_uom_qty": self.quantity,
                "is_rental": True,
                "pickup_date": self.pickup_date,
                "return_date": self.return_date,
                "price_unit": self.unit_price,
            }
            self.sale_order_id.write(
                {"pickup_date": self.pickup_date, "return_date": self.return_date}
            )
            self.sale_order_id.write({"order_line": [(0, 0, vals)]})
        if is_edit_rental_line:
            order_line = self.env["sale.order.line"].browse(
                self._context.get('order_line')
            )
            order_line.write(
                {
                    "product_id": self.product_id.id,
                    "name": "%s\n%s to %s"
                    % (product_name, self.pickup_date, self.return_date),
                    "product_uom_qty": self.quantity,
                    "is_rental": True,
                    "pickup_date": self.pickup_date,
                    "return_date": self.return_date,
                    "price_unit": self.unit_price,
                }
            )
