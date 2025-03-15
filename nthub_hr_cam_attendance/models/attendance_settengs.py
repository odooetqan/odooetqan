# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class AttendanceConfig(models.TransientModel):
    _inherit = ['res.config.settings']

    long = fields.Char()
    lat = fields.Char()

    working_from = fields.Float()
    working_to = fields.Float()

    max_distance = fields.Integer()

    behavior = fields.Selection([('none','None'), ('record','check in at the same time of check out')])
    hr_attendance_face_rec = fields.Boolean()
    def set_values(self):
        super(AttendanceConfig, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "nthub_hr_cam_attendance.long", self.long)
        self.env['ir.config_parameter'].sudo().set_param(
            "nthub_hr_cam_attendance.lat", self.lat)
        self.env['ir.config_parameter'].sudo().set_param(
            "nthub_hr_cam_attendance.working_from", self.working_from)
        self.env['ir.config_parameter'].sudo().set_param(
            "nthub_hr_cam_attendance.working_to", self.working_to)
        self.env['ir.config_parameter'].sudo().set_param(
            "nthub_hr_cam_attendance.behavior", self.behavior)
        self.env['ir.config_parameter'].sudo().set_param(
            "nthub_hr_cam_attendance.hr_attendance_face_rec", self.behavior)
        self.env['ir.config_parameter'].sudo().set_param(
            "nthub_hr_cam_attendance.max_distance", self.max_distance)

    @api.model
    def get_values(self):
        res = super(AttendanceConfig, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['long'] = float(get_param('nthub_hr_cam_attendance.long'))
        res['lat'] = float(get_param('nthub_hr_cam_attendance.lat'))
        res['working_from'] = float(get_param('nthub_hr_cam_attendance.working_from'))
        res['working_to'] = float(get_param('nthub_hr_cam_attendance.working_to'))
        res['behavior'] = get_param('nthub_hr_cam_attendance.behavior')
        res['hr_attendance_face_rec'] = get_param('nthub_hr_cam_attendance.hr_attendance_face_rec')
        res['max_distance'] = get_param('nthub_hr_cam_attendance.max_distance')
        return res