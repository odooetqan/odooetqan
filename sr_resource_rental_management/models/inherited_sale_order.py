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
from datetime import datetime, timedelta
from odoo.addons.sale_stock.models.sale_order import SaleOrder
from odoo.exceptions import ValidationError


class srSaleOrder(models.Model):
    _inherit = "sale.order"

    rental_status = fields.Selection(
        [
            ("reserved", "Reserved"),
            ("pickup", "Picked-up"),
            ("return", "Returned"),
            ("cancel", "Cancelled"),
        ]
    )
    pickup_date = fields.Date(string="Pickup Date", default=datetime.now().date())
    return_date = fields.Date(
        string="Return Date", default=datetime.now().date() + timedelta(days=1)
    )
    is_rental = fields.Boolean("Is Rental")
    is_pickup = fields.Boolean("Is Picked-up")
    is_returned = fields.Boolean("Is Returned")
    is_late = fields.Boolean("Is Late")

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New") and vals.get("is_rental"):
            seq_date = None
            if "date_order" in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals["date_order"])
                )
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "rental.order", sequence_date=seq_date
            ) or _("New")
        return super(srSaleOrder, self).create(vals=vals)

    def action_confirm(self):
        return super(SaleOrder, self).action_confirm()

    def send_mail_pickup(self):
        reminder_pickup_order_days = self.env["ir.config_parameter"].get_param(
            "sr_resource_rental_management.reminder_pickup_order_days"
        )
        template_id = self.env.ref(
            "sr_resource_rental_management.email_template_pickup"
        )
        current_date = datetime.now().date()
        order_line = self.env["sale.order.line"].search(
            [("is_rental", "=", True), ("pickup_date", "<", current_date)]
        )
        order_line = order_line.filtered(
            lambda line: line.check_send_mail_pickup(reminder_pickup_order_days, line)
        )
        sale_ids = order_line.mapped("order_id")
        if sale_ids:
            for sale_id in sale_ids:
                template_id.send_mail(sale_id.id, force_send=True)

    def send_mail_return(self):
        reminder_return_order_days = self.env["ir.config_parameter"].get_param(
            "sr_resource_rental_management.reminder_return_order_days"
        )
        template_id = self.env.ref(
            "sr_resource_rental_management.email_template_return"
        )
        current_date = datetime.now().date()
        order_line = self.env["sale.order.line"].search(
            [("is_rental", "=", True), ("return_date", "<", current_date)]
        )
        order_line = order_line.filtered(
            lambda line: line.check_send_mail_return(reminder_return_order_days, line)
        )
        sale_ids = order_line.mapped("order_id")
        if sale_ids:
            for sale_id in sale_ids:
                template_id.send_mail(sale_id.id, force_send=True)

    def action_confirm(self):
        super(SaleOrder, self).action_confirm()
        self.write({"rental_status": "reserved"})

    def create_rental_order_line(self, status):
        lines = []
        for line in self.order_line:
            vals = {
                "product_id": line.product_id.id,
                "order_line_id": line.id,
                "qty_reserved": line.product_uom_qty,
                "rental_order_status": status,
                "lot_ids": [(6, 0, line.lot_ids.ids)],
                "qty_delivered": line.qty_delivered,
                "qty_returned": line.qty_delivered,
                "is_late": line.is_late,
            }
            lines.append((0, 0, vals))
        return lines

    def action_pickup(self):
        is_late = False
        current_date = datetime.now().date()
        if current_date < self.pickup_date:
            is_late = False
        else:
            is_late = True
        lines = self.create_rental_order_line(status="pickup")
        context = {
            "default_sale_order_id": self.id,
            "default_rental_order_status": "pickup",
            "default_rental_order_line_ids": lines,
            "default_is_pickup": True,
            "default_is_late": is_late,
        }
        return {
            "name": _("Rental Order Line"),
            "type": "ir.actions.act_window",
            "res_model": "sr.rental.order.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    def action_return(self):
        is_late = False
        current_date = datetime.now().date()
        if current_date < self.return_date:
            is_late = False
        else:
            is_late = True
        lines = self.create_rental_order_line(status="return")
        context = {
            "default_sale_order_id": self.id,
            "default_rental_order_status": "return",
            "default_rental_order_line_ids": lines,
            "default_is_return": True,
            "default_is_late": is_late,
        }
        return {
            "name": _("Rental Order Line"),
            "type": "ir.actions.act_window",
            "res_model": "sr.rental.order.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    def add_rental_product(self):
        context = {
            "default_sale_order_id": self.id,
            "default_pickup_date": datetime.now(),
            "default_return_date": datetime.now() + timedelta(days=1),
        }
        return {
            "name": _("Rental Product"),
            "type": "ir.actions.act_window",
            "res_model": "sr.rental.product.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }


class srSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_id = fields.Many2one(group_expand="_read_group_product_ids")
    rental_status = fields.Selection(
        [
            ("reserved", "Reserved"),
            ("pickup", "Picked-up"),
            ("return", "Returned"),
            ("cancel", "Cancelled"),
        ],
        group_expand="_read_group_report_line_status",
    )
    pickup_date = fields.Date(string="Pickup Date")
    return_date = fields.Date(string="Return Date")
    returned_qty = fields.Float("Returned")
    lot_ids = fields.Many2many("stock.production.lot", string="Serial Numbers")
    is_rental = fields.Boolean("Is Rental")
    is_pickup = fields.Boolean("Is Picked-up")
    is_returned = fields.Boolean("Is Returned")
    is_late = fields.Boolean("Is Late")
    date_from = fields.Date(
        "Date From", required=True, index=True, default=fields.Date.context_today
    )
    date_to = fields.Date(
        "Date To", required=True, index=True, default=fields.Date.context_today
    )

    def action_rental(self):
        context = {
            "is_edit_rental_line": True,
            "order_line": self.id,
            "default_product_id": self.product_id.id,
            "default_pickup_date": self.pickup_date,
            "default_return_date": self.return_date,
            "default_quantity": self.product_uom_qty,
            "default_unit_price": self.price_unit,
        }
        return {
            "name": _("Rental Product"),
            "type": "ir.actions.act_window",
            "res_model": "sr.rental.product.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "context": context,
        }

    def check_send_mail_pickup(self, reminder_pickup_order_days, line):
        current_date = datetime.now().date()
        if int(reminder_pickup_order_days) <= abs(
            (current_date - line.pickup_date).days
        ):
            return True
        return False

    def check_send_mail_return(self, reminder_return_order_days, line):
        current_date = datetime.now().date()
        if int(reminder_return_order_days) <= abs(
            (current_date - line.return_date).days
        ):
            return True
        return False

    def check_pickup(self):
        current_date = datetime.now().date()
        if self.pickup_date and self.pickup_date < current_date:
            return True
        return False

    def check_return(self):
        current_date = datetime.now().date()
        if self.return_date and self.return_date < current_date:
            return True
        return False

    def get_tax_name(self):
        taxes_name = ""
        for tax in self.tax_id:
            if not taxes_name:
                taxes_name += "%s" % (tax.name)
            else:
                taxes_name += "%s," % (tax.name)
        return taxes_name

    def create_stok_move_line(self, stock_move, stock_quant):
        return self.env["stock.move.line"].create(
            stock_move._prepare_move_line_vals(reserved_quant=stock_quant)
        )

    def create_stok_move(self, quantity, lot_ids, source_location, dest_location):
        return self.env["stock.move"].create(
            {
                "product_id": self.product_id.id,
                "product_uom_qty": len(lot_ids) if lot_ids else quantity,
                "product_uom": self.product_id.uom_id.id,
                "location_id": source_location.id,
                "location_dest_id": dest_location.id,
                "partner_id": self.order_partner_id.id,
                "sale_line_id": self.id,
                "name": _("Rental move :") + " %s" % (self.order_id.name),
            }
        )

    def storable_product_picked_move(self, lot_ids, source_location, dest_location):
        quantity = 0.0
        if not lot_ids:
            return
        stock_move = self.create_stok_move(
            quantity, lot_ids, source_location, dest_location
        )
        for lot in lot_ids:
            stock_quant = self.env["stock.quant"]._gather(
                self.product_id, source_location, lot
            )
            stock_quant = stock_quant.filtered(lambda quant: quant.quantity == 1.0)
            if not stock_quant:
                raise ValidationError(
                    _(
                        "No valid quant has been found in location %s for serial number"
                        " %s !"
                    )
                    % (source_location.name, lot.name)
                )
            move_line = self.create_stok_move_line(stock_move, stock_quant)
            move_line["qty_done"] = 1
        stock_move._action_done()

    def storable_product_return_move(self, lot_ids, source_location, dest_location):
        if not lot_ids:
            return
        stock_move = self.env["stock.move"].search(
            [
                ("sale_line_id", "=", self.id),
                ("location_id", "=", source_location.id),
                ("location_dest_id", "=", dest_location.id),
            ]
        )
        for move in stock_move.mapped("move_line_ids"):
            if move.lot_id.id in lot_ids.ids:
                move.qty_done = 0.0
        stock_move.product_uom_qty -= len(lot_ids)

    def consume_picked_move(self, qty, source_location, dest_location):
        lot_ids = False
        move_id = self.create_stok_move(qty, lot_ids, source_location, dest_location)
        move_id._action_assign()
        move_id._set_quantity_done(qty)
        move_id._action_done()

    def consume_return_move(self, qty, source_location, dest_location):
        move_ids = self.env["stock.move"].search(
            [
                ("sale_line_id", "=", self.id),
                ("location_id", "=", source_location.id),
                ("location_dest_id", "=", dest_location.id),
            ],
            order="date desc",
        )
        for move in move_ids.mapped("move_line_ids"):
            qty -= move.qty_done
            move.qty_done = 0.0 if qty > 0.0 else -qty
            if qty <= 0.0:
                return True
        return qty <= 0.0
