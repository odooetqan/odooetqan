from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attendance_location = fields.Integer(string='Attendance Location')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['attendance_location'] = int(self.env['ir.config_parameter'].sudo().get_param('hr_attendance_map_geolocation.attendance_location', default=100))
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('hr_attendance_map_geolocation.attendance_location', self.attendance_location)
        super(ResConfigSettings, self).set_values()