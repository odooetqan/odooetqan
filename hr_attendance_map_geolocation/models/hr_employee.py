# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from geopy import distance
from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    active_location = fields.Boolean('Active location', default=False)
    geolocation = fields.Char('Geolocation', default=False)
    latitude = fields.Float('Latitudue', digits="Location", compute='_compute_geolocation')
    longitude = fields.Float('Longitude', digits="Location", compute='_compute_geolocation')

    @api.depends('geolocation')
    def _compute_geolocation(self):
        self.ensure_one()
        for rec in self:
            if rec.active_location:
                if not rec.geolocation:
                    if rec.address_id.partner_latitude and rec.address_id.partner_longitude:
                        rec.latitude = rec.address_id.partner_latitude
                        rec.longitude = rec.address_id.partner_longitude
                    else:                         
                        raise ValidationError( _('Please enable the geolocation of work address!!'))
                else:
                    if not ',' in rec.geolocation:
                        raise ValidationError("Invalid latitude and longitude")
                    else:
                        geol = rec.geolocation.split(",")
                        rec.latitude = geol[0]
                        rec.longitude = geol[1]
            else:
                rec.latitude = False
                rec.longitude = False

    
    def check_workplace(self):
        lat = str(self.address_id.partner_latitude)
        lng = str(self.address_id.partner_longitude)
        if self.geolocation:
            workplace = str(self.geolocation)
        else:
            workplace = lat+','+lng
        return {
            'type': 'ir.actions.act_url',
            'url': 'http://maps.google.com/maps?q=' + workplace,
            'target': '_new',
        }

    def attendance_manual(self, next_action, entered_pin=False, location=False):
        self.ensure_one()
        params = self.env['ir.config_parameter'].sudo()
        attendance_location = int(params.get_param('hr_attendance_map_geolocation.attendance_location', default=100))
        location = self.env.context.get("attendance_location", location)
        if self.active_location:
            lat = location[0]
            lng = location[1]
            act_latitude = self.latitude
            act_longitude = self.longitude
            position = distance.distance((act_latitude, act_longitude), (lat, lng)).km
            if (position*1000) <= attendance_location:
                return super(HrEmployee, self.with_context(attendance_location=location)).attendance_manual(next_action, entered_pin)
            else:
                raise ValidationError("You can only do check in/out within Active Location")
        else:
            return super(HrEmployee, self.with_context(attendance_location=location)).attendance_manual(next_action, entered_pin)


    def _attendance_action_change(self):
        res = super()._attendance_action_change()
        location = self.env.context.get("attendance_location", False)
        if location:
            if self.attendance_state == "checked_in":
                res.write(
                    {
                        "check_in_latitude": location[0],
                        "check_in_longitude": location[1],
                    }
                )
            else:
                res.write(
                    {
                        "check_out_latitude": location[0],
                        "check_out_longitude": location[1],
                    }
                )
        return res