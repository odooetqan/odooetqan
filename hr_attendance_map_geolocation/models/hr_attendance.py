# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_latitude = fields.Float("Check-in Latitude", digits="Location", readonly=True)
    check_in_longitude = fields.Float("Check-in Longitude", digits="Location", readonly=True)

    check_out_latitude = fields.Float("Check-out Latitude", digits="Location", readonly=True)
    check_out_longitude = fields.Float("Check-out Longitude", digits="Location", readonly=True)

    def check_location_in(self):
        in_latitude = str(self.check_in_latitude)
        in_longitude = str(self.check_in_longitude)

        check_in_location = in_latitude +','+ in_longitude
        return {
            'type': 'ir.actions.act_url',
            'url': 'http://maps.google.com/maps?q='+check_in_location,
            'target': '_new',
        }

    def check_location_out(self):
        out_latitude = str(self.check_out_latitude)
        out_longitude = str(self.check_out_longitude)
        check_out_location = out_latitude +','+ out_longitude
        return {
            'type': 'ir.actions.act_url',
            'url': 'http://maps.google.com/maps?q='+check_out_location,
            'target': '_new',
        }
