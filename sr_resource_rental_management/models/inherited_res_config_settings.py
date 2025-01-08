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


class srResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    reminder_pickup_order_days = fields.Integer("Reminder Pickup Order (After Days)", config_parameter="sr_resource_rental_management.reminder_pickup_order_days")
    reminder_return_order_days = fields.Integer("Reminder Return Order (After Days)", config_parameter="sr_resource_rental_management.reminder_return_order_days")

    def set_values(self):
        super(srResConfigSettings, self).set_values()
        IrConfigParamObj = self.env['ir.config_parameter']
        IrConfigParamObj.set_param(
            'sr_resource_rental_management.reminder_pickup_order_days',
            self.reminder_pickup_order_days,
        )
        IrConfigParamObj.set_param(
            'sr_resource_rental_management.reminder_return_order_days',
            self.reminder_return_order_days,
        )
