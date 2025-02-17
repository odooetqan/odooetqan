from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

class PortalAttendance(http.Controller):

    @http.route('/portal/request_attendance_correction', type='http', auth="user", methods=['POST'], website=True)
    def request_attendance_correction(self, **kwargs):
        """ Handles attendance correction requests from the portal """
        
        # Retrieve form data
        attendance_id = int(kwargs.get('attendance_id'))
        corrected_check_in = kwargs.get('corrected_check_in')
        corrected_check_out = kwargs.get('corrected_check_out')
        correction_reason = kwargs.get('correction_reason')

        # Ensure attendance record exists
        attendance = request.env['hr.attendance'].sudo().browse(attendance_id)
        if not attendance.exists():
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

        return request.redirect('/my/attendance')
