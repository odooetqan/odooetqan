from math import radians, sin, cos, sqrt, atan2
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, values):
        attendance = super(HrAttendance, self).create(values)
        attendance._check_company_range()
        return attendance

    def write(self, values):
        res = super(HrAttendance, self).write(values)
        self._check_company_range()
        return res

    def _compute_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the earth in kilometers
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Calculate the change in coordinates
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        # Apply Haversine formula
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance

    def _check_company_range(self):
        company = self.env.company
        company_latitude = company.company_latitude or 0.000000
        company_longitude = company.company_longitude or 0.0000000
        allowed_distance_meters = company.allowed_distance or 1100  # Default allowed distance is 1100 meters

        _logger.info(f'company Latitude: {company_latitude}, company Longitude: {company_longitude}, Allowed Distance: {allowed_distance_meters} meters')

        for attendance in self:
            if not (attendance.in_latitude and attendance.in_longitude):
                raise UserError(_("Oops! It seems we're missing your location information. Could you please allow us to access your location so we can proceed?"))

            # Compute the distance between company and attendance location
            distance_meters = self._compute_distance(
                company_latitude, company_longitude,
                attendance.in_latitude, attendance.in_longitude
            ) * 1000  # Convert kilometers to meters

            if distance_meters > allowed_distance_meters:
                raise UserError(_(
                    "You are outside the allowed range of the company location. "
                    "Please ensure that you are within the company Location. "
                    "The distance exceeds the allowed distance."
                ))
