# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################
from odoo import api, models, _
from odoo.osv import expression


class srStockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    @api.model
    def _name_search(
        self, name, args=None, operator='ilike', limit=100, name_get_uid=None
    ):
        super(srStockProductionLot, self)._name_search(
            name=name,
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )
        context = self._context
        product_id = context.get("product_id")
        is_pickup = context.get("is_pickup")
        args = args or []
        domain = []
        if product_id and is_pickup:
            lot_ids = self.search([('product_id', '=', product_id)])
            line = self.env["sale.order.line"].search(
                [('lot_ids', 'in', lot_ids.ids), ('is_pickup', '=', True)]
            )
            domain = [
                ('id', 'not in', line.lot_ids.ids),
                ('product_id', '=', product_id),
            ]
        # if name:
        #     domain += ['|', ('name', operator, name), ('partner_ref', operator, name)]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )
