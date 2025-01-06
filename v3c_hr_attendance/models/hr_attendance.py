import werkzeug.urls

from odoo import fields, models, api

MAP_DEFAULT_ZOOM = 13


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_latitude = fields.Float("Check-in Latitude", digits=(10, 7), readonly=True)
    check_in_longitude = fields.Float("Check-in Longitude", digits=(10, 7), readonly=True)
    check_out_latitude = fields.Float("Check-out Latitude", digits=(10, 7), readonly=True)
    check_out_longitude = fields.Float("Check-out Longitude", digits=(10, 7), readonly=True)
    check_in_url = fields.Char('Check In Location', compute='_compute_check_in_url')
    check_out_url = fields.Char('Check Out Location', compute='_compute_check_out_url')

    @api.depends('check_in_latitude', 'check_in_longitude')
    def _compute_check_in_url(self):
        for rec in self:
            # print('\n session===', self._context)
            # print('\n rec.check_in_latitude===', rec.check_in_latitude)

            # check if check in location is blank
            if rec.check_in_latitude and rec.check_in_longitude:
                params = {
                    'q': '%s,%s' % (rec.check_in_latitude or '', rec.check_in_longitude or ''), 'z': MAP_DEFAULT_ZOOM,
                }
            else:
                params = ""

            if params == "":
                # Location not found then check out url is blank string
                rec.check_in_url = ""
            else:
                # Location found then show google map URL
                rec.check_in_url = '%s?%s' % ('https://maps.google.com/maps', werkzeug.urls.url_encode(params or None))

    @api.depends('check_out_latitude', 'check_out_longitude')
    def _compute_check_out_url(self):
        for rec in self:

            # check if check out location is blank
            if rec.check_out_latitude and rec.check_out_longitude:
                params = {
                    'q': '%s,%s' % (rec.check_out_latitude or '', rec.check_out_longitude or ''), 'z': MAP_DEFAULT_ZOOM,
                }
            else:
                params = ""

            if params == "":
                # Location not found then check out url is blank string
                rec.check_out_url = ""
            else:
                # Location found then show google map URL
                rec.check_out_url = '%s?%s' % ('https://maps.google.com/maps', werkzeug.urls.url_encode(params or None))
