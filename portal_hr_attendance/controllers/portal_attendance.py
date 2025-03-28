from odoo import http, fields
from odoo.http import request
import pytz
import json

class PortalAttendanceController(http.Controller):
    @http.route(['/my/attendance_check'], type='http', auth='user', website=True)
    def portal_my_attendance_check(self, **kwargs):
        """
        Display an attendance page with a "Check In" or "Check Out" button
        depending on the employee's current status.
        """
        user = request.env.user
        # Find the employee record linked to this portal user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not employee:
            # If there's no employee, redirect or show an error
            return request.redirect('/my/home')

        # Check the last attendance record for this employee
        last_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
        ], order='check_in desc', limit=1)

        # Determine if currently 'checked in' or not
        is_checked_in = False
        if last_attendance and not last_attendance.check_out:
            is_checked_in = True
            is_checked_out = False
        else:
            is_checked_out= True
            is_checked_in = False

        # Calculate "Today's hours" (optional). You might sum attendances for today:
        # This is just a simple example:
        today = fields.Date.today()
        attendances_today = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', today),
        ])
        total_hours = sum(a.worked_hours for a in attendances_today)

        # Pass data to QWeb template
        values = {
            'employee_name': employee.name,
            'is_checked_in': is_checked_in,
            'is_checked_out': is_checked_out,
            'total_hours': total_hours,
        }
        return request.render('portal_hr_attendance.portal_my_attendance_check', values)

    @http.route(['/my/attendance/toggle'], type='json', auth='user', methods=['POST'], website=True)
    def toggle_attendance(self, **kwargs):
        """
        A JSON route to toggle Check In or Check Out for the current user.
        Return JSON with success/error messages.
        """
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return {'success': False, 'message': 'No employee linked to this user.'}

        attendance_model = request.env['hr.attendance'].sudo()

        # Check if there's an open attendance
        last_attendance = attendance_model.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)

        if last_attendance:
            # If we have an open attendance, then we do "Check Out"
            last_attendance.write({'check_out': fields.Datetime.now()})
            return {'success': True, 'message': 'Checked Out successfully!'}
        else:
            # Otherwise, "Check In"
            attendance_model.create({
                'employee_id': employee.id,
                'check_in': fields.Datetime.now(),
            })
            return {'success': True, 'message': 'Checked In successfully!'}
