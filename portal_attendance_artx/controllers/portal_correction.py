from odoo import http
from odoo.http import request
import logging
from datetime import datetime


_logger = logging.getLogger(__name__)

class PortalAttendance(http.Controller):

    # @http.route('/portal/request_attendance_correction', type='http', auth="user", methods=['POST'], website=True)
    @http.route('/portal/request_attendance_correction', type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def request_attendance_correction(self, **kwargs):
        """ Handles attendance correction requests from the portal """

        _logger.info("✅ Attendance Correction Request Received: %s", kwargs)

        # Ensure `attendance_id` is valid
        attendance_id = kwargs.get('attendance_id')
        if not attendance_id or not attendance_id.isdigit():
            _logger.warning("❌ Invalid attendance_id: %s", attendance_id)
            return request.redirect('/my/attendance')  # Redirect if invalid

        attendance_id = int(attendance_id)
        corrected_check_in = kwargs.get('corrected_check_in')
        corrected_check_out = kwargs.get('corrected_check_out')
        correction_reason = kwargs.get('correction_reason')


        #######################################################################################################################
        # Convert datetime format from HTML5 datetime-local input (2025-01-27T18:26) to Odoo format (2025-01-27 18:26:00)
        try:
            corrected_check_in = datetime.strptime(corrected_check_in, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
            corrected_check_out = datetime.strptime(corrected_check_out, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            _logger.error("❌ Date conversion error: %s", e)
            return request.redirect('/my/attendance')

        # Ensure attendance record exists
        # attendance = request.env['hr.attendance
        #######################################################################################################################
        
        # Ensure attendance record exists
        attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
        if not attendance.exists():
            _logger.warning("❌ Attendance record not found for ID: %d", attendance_id)
            return request.redirect('/my/attendance')  # Redirect back if record not found

        # Create a correction request
        correction = request.env['hr.attendance.correction'].sudo().create({
            'employee_id': attendance.employee_id.id,
            'attendance_id': attendance.id,
            'original_check_in': attendance.check_in,
            'original_check_out': attendance.check_out,
            'corrected_check_in': corrected_check_in,
            'corrected_check_out': corrected_check_out,
            'reason': correction_reason,
            'state': 'pending',  # Set status to pending approval
        })

        if correction:
            _logger.info("✅ Successfully Created Correction Request: %s", correction.id)
        else:
            _logger.error("❌ Failed to Create Correction Request")

        return request.redirect('/my/attendance')

