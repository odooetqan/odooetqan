from odoo import http, fields
from odoo.http import request
import logging
from datetime import datetime
import base64

_logger = logging.getLogger(__name__)
class PortalAttendance(http.Controller):

    @http.route('/portal/request_attendance_correction', type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def request_attendance_correction(self, **kwargs):
        attendance_id = int(kwargs.get('attendance_id', 0))
        corrected_time = kwargs.get('corrected_time')  # HH:MM format
        correction_type = kwargs.get('correction_type')  # 'check_in' or 'check_out'
        correction_reason = kwargs.get('correction_reason')

        attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
        if not attendance.exists() or not corrected_time or correction_type not in ['check_in', 'check_out']:
            return request.redirect('/my/attendance')

        correction = request.env['hr.attendance.correction'].sudo().create({
            'employee_id': attendance.employee_id.id,
            'attendance_id': attendance.id,
            'original_check_in': attendance.check_in,
            'original_check_out': attendance.check_out,
            'corrected_time': corrected_time,
            'correction_type': correction_type,
            'reason': correction_reason,
        })
        
        # 2) Save uploaded files as ir.attachment and link to M2M field
        files = request.httprequest.files.getlist('attachments')  # Werkzeug FileStorage list
        att_ids = []
        for f in files:
            if not f or not f.filename:
                continue
            data = f.read()
            if not data:
                continue
            att = request.env['ir.attachment'].sudo().create({
                'name': f.filename,
                'datas': base64.b64encode(data),
                'mimetype': f.content_type,
                # Attach to the record (so it appears in chatter)
                'res_model': 'hr.attendance.correction',
                'res_id': correction.id,
            })
            att_ids.append(att.id)

        if att_ids:
            correction.sudo().write({'attachment': [(6, 0, att_ids)]})
            

        return request.redirect('/my/attendance')


# class PortalAttendance(http.Controller):

#     # @http.route('/portal/request_attendance_correction', type='http', auth="user", methods=['POST'], website=True)
#     @http.route('/portal/request_attendance_correction', type='http', auth="user", methods=['POST'], website=True, csrf=False)
#     def request_attendance_correction(self, **kwargs):
#         """ Handles attendance correction requests from the portal """

#         _logger.info("✅ Attendance Correction Request Received: %s", kwargs)

#         # Ensure `attendance_id` is valid
#         attendance_id = kwargs.get('attendance_id')
#         if not attendance_id or not attendance_id.isdigit():
#             _logger.warning("❌ Invalid attendance_id: %s", attendance_id)
#             return request.redirect('/my/attendance')  # Redirect if invalid

#         attendance_id = int(attendance_id)
#         corrected_check_in = kwargs.get('corrected_check_in')
#         corrected_check_out = kwargs.get('corrected_check_out')
#         correction_reason = kwargs.get('correction_reason')


#         #######################################################################################################################
#         # Convert datetime format from HTML5 datetime-local input (2025-01-27T18:26) to Odoo format (2025-01-27 18:26:00)
#         try:
#             corrected_check_in = datetime.strptime(corrected_check_in, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
#             corrected_check_out = datetime.strptime(corrected_check_out, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
#         except ValueError as e:
#             _logger.error("❌ Date conversion error: %s", e)
#             return request.redirect('/my/attendance')

#         # Ensure attendance record exists
#         # attendance = request.env['hr.attendance
#         #######################################################################################################################
        
#         # Ensure attendance record exists
#         attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
#         if not attendance.exists():
#             _logger.warning("❌ Attendance record not found for ID: %d", attendance_id)
#             return request.redirect('/my/attendance')  # Redirect back if record not found

#         # Create a correction request
#         correction = request.env['hr.attendance.correction'].sudo().create({
#             'employee_id': attendance.employee_id.id,
#             'attendance_id': attendance.id,
#             'original_check_in': attendance.check_in,
#             'original_check_out': attendance.check_out,
#             'corrected_check_in': corrected_check_in,
#             'corrected_check_out': corrected_check_out,
#             'reason': correction_reason,
#             'state': 'pending',  # Set status to pending approval
#         })

#         if correction:
#             _logger.info("✅ Successfully Created Correction Request: %s", correction.id)
#         else:
#             _logger.error("❌ Failed to Create Correction Request")

#         return request.redirect('/my/attendance')

