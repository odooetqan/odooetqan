# -*- coding: utf-8 -*-
# from odoo import http


# class AttendanceLocation(http.Controller):
#     @http.route('/attendance_location/attendance_location', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/attendance_location/attendance_location/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('attendance_location.listing', {
#             'root': '/attendance_location/attendance_location',
#             'objects': http.request.env['attendance_location.attendance_location'].search([]),
#         })

#     @http.route('/attendance_location/attendance_location/objects/<model("attendance_location.attendance_location"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('attendance_location.object', {
#             'object': obj
#         })

