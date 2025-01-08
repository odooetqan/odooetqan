# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################
from odoo import fields, api, models, _
from datetime import datetime, time
from odoo.exceptions import ValidationError


class srRentalOrder(models.TransientModel):
    _name = "sr.rental.order.wizard"
    _description = "Sr Rental Order Wizard"

    sale_order_id = fields.Many2one(
        'sale.order', string="Sale Order", required=True, ondelete='cascade'
    )
    rental_order_line_ids = fields.One2many(
        'sr.rental.order.line.wizard', 'rental_order_id', string="Rental Order Line"
    )
    rental_order_status = fields.Selection(
        selection=[('pickup', 'Pickup'), ('return', 'Return')],
        string="Rental Order Status",
    )
    is_pickup = fields.Boolean("Is Picked-up")
    is_returned = fields.Boolean("Is Returned")
    is_late = fields.Boolean("Is Late")

    def date_diff_in_seconds(self, dt2, dt1):
        timedelta = dt2 - dt1
        return timedelta.days * 24 * 3600 + timedelta.seconds

    def dhms_from_seconds(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        return (days, hours, minutes, seconds)

    def add_line(self):
        current_date = fields.Datetime.now().date()
        for line in self.rental_order_line_ids:
            if line.rental_order_status == "pickup":
                self.sale_order_id.write(
                    {
                        "is_pickup": True,
                        "rental_status": "pickup",
                        "is_late": line.is_late,
                    }
                )
                order_line = line.order_line_id
                order_line.mapped('company_id').filtered(
                    lambda company: not company.sr_rental_loc_id
                )._create_rental_location()
                source_location = order_line.company_id.sr_rental_loc_id
                dest_location = self.sale_order_id.warehouse_id.lot_stock_id
                if not line.lot_ids:
                    if order_line.qty_delivered < 0:
                        order_line.consume_return_move(
                            -order_line.qty_returned, source_location, dest_location
                        )
                else:
                    order_line.storable_product_picked_move(
                        line.lot_ids, dest_location, source_location
                    )

                order_line.write(
                    {
                        "is_pickup": True,
                        "rental_status": "pickup",
                        "lot_ids": [(6, 0, line.lot_ids.ids)],
                        "is_late": line.is_late,
                        "qty_delivered": line.qty_delivered,
                    }
                )

            if line.rental_order_status == "return":
                delay_duration = 0.0
                if line.order_line_id.return_date < current_date:
                    days, hours, minutes, seconds = self.dhms_from_seconds(
                        self.date_diff_in_seconds(
                            current_date, line.order_line_id.return_date
                        )
                    )
                    if days:
                        delay_duration += days * line.product_id.list_price
                delay_duration = delay_duration + line.order_line_id.price_unit
                self.sale_order_id.write(
                    {
                        "is_pickup": False,
                        "is_returned": True,
                        "rental_status": "return",
                        "is_late": line.is_late,
                    }
                )
                order_line = line.order_line_id
                order_line.mapped('company_id').filtered(
                    lambda company: not company.sr_rental_loc_id
                )._create_rental_location()
                source_location = order_line.company_id.sr_rental_loc_id
                dest_location = self.sale_order_id.warehouse_id.lot_stock_id
                if not order_line.lot_ids:
                    if order_line.returned_qty < 0:
                        order_line.consume_return_move(
                            -order_line.qty_returned, source_location, dest_location
                        )
                else:
                    order_line.storable_product_return_move(
                        order_line.lot_ids, dest_location, source_location
                    )
                order_line.write(
                    {
                        "is_pickup": False,
                        "is_returned": True,
                        "qty_delivered": line.qty_delivered,
                        "rental_status": "return",
                        "returned_qty": line.qty_returned,
                        "price_unit": delay_duration,
                        "is_late": line.is_late,
                    }
                )


class srRentalOrderLine(models.TransientModel):
    _name = "sr.rental.order.line.wizard"
    _description = "Sr Rental Order Line Wizard"

    rental_order_id = fields.Many2one("sr.rental.order.wizard", string="Rental Order")
    rental_order_status = fields.Selection(
        related='rental_order_id.rental_order_status', string="Rental Order Status"
    )
    order_line_id = fields.Many2one(
        'sale.order.line', required=True, ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, ondelete='cascade'
    )
    lot_ids = fields.Many2many(
        "stock.production.lot", string="Serial Number", required=True
    )
    qty_reserved = fields.Float("Reserved")
    qty_delivered = fields.Float("Picked-up")
    qty_returned = fields.Float("Returned")
    is_pickup = fields.Boolean("Is Picked-up")
    is_returned = fields.Boolean("Is Returned")
    is_late = fields.Boolean("Is Late")

    @api.onchange("lot_ids")
    def onchange_lot_ids(self):
        if self.order_line_id.product_uom_qty > self.qty_delivered:
            qty = 0.0
            for lot in self.lot_ids:
                if (
                    self.rental_order_status != "return"
                    and self.qty_delivered != self.order_line_id.product_uom_qty
                ):
                    qty += lot.product_qty
            self.qty_delivered = qty
