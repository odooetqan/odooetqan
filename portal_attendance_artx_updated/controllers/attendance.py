from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from odoo import http, fields
import json
import pytz 


import logging
_logger = logging.getLogger(__name__)


class PortalAttendance(http.Controller):
    @http.route(['/my/attendance'], type='http', auth='user', website=True)
    def portal_my_attendance(self, **kw):
        user = request.env.user
        employee = request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)

        attendance_records = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id)
        ], order="check_in desc")

        # Convert check_in and check_out to user's timezone
        user_tz = user.tz or 'UTC'
        tz = pytz.timezone(user_tz)

        def convert_dt(dt):
            if dt:
                return fields.Datetime.context_timestamp(request.env.user, dt).strftime('%Y-%m-%d %H:%M')
            return ''

        for record in attendance_records:
            record.check_in = convert_dt(record.check_in)
            record.check_out = convert_dt(record.check_out)

        values = {
            'attendance_records': attendance_records,
        }
        return request.render("portal_attendance_artx_updated.portal_my_attendance", values)

    @http.route('/portal/get_attendance_status', type='http', auth="user", methods=['GET'], csrf=False)
    def get_attendance_status(self, **kwargs):
        # Fetch the currently logged-in user
        user = request.env.user
        print('Logged-in user:', user.name, user.id)

        # Fetch the employee associated with the user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            print('No employee found for user:', user.id)
            response_data = {
                'success': False,
                'message': 'No employee associated with this user.'
            }
            return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

        print('Employee found:', employee.name, employee.id)

        # Search for attendance records where the user is checked in (check_out is False)
        attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)

        if attendance:
            check_in_time = attendance.check_in
            print('Attendance record found with check-in:', check_in_time)
            response_data = {
                'success': True,
                'message': 'Currently checked in',
                'check_in': check_in_time.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
            }
        else:
            print('No active attendance (checked in) record found.')
            response_data = {
                'success': True,
                'message': 'Currently checked out',
            }

        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])


    @http.route('/portal/add_attendance', type='json', auth='user', methods=['POST'], csrf=False)
    def add_attendance(self, **kwargs):
        """ Handle Employee Check-in """
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not employee:
            return {'success': False, 'message': 'الموظف غير موجود'}

        last_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id)
        ], order="check_in desc", limit=1)

        if last_attendance and not last_attendance.check_out:
            return {'success': False, 'message': 'يجب تسجيل الخروج أولاً'}

        attendance = request.env['hr.attendance'].sudo().create({
            'employee_id': employee.id,
            'check_in': fields.Datetime.now(),
        })

        return {'success': True, 'message': 'تم تسجيل الحضور بنجاح!'}

    @http.route('/portal/check_out', type='json', auth='user', methods=['POST'], csrf=False)
    def check_out(self, **kwargs):
        """ Handle Employee Check-out """
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not employee:
            return {'success': False, 'message': 'الموظف غير موجود'}

        last_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], order="check_in desc", limit=1)

        if not last_attendance:
            return {'success': False, 'message': 'لا يوجد تسجيل دخول مفتوح'}

        last_attendance.sudo().write({'check_out': fields.Datetime.now()})

        return {'success': True, 'message': 'تم تسجيل الخروج بنجاح!'}

####################### End  portal Attendance ##########################################

# # --- leaves  
class PortalLeaves(http.Controller):

    @http.route('/my/leaves', type='http', auth='user', website=True)
    def portal_my_leaves(self, **kwargs):
        # Fetch leave requests for the logged-in user
        employee = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)], limit=1)
        leave_records = request.env['hr.leave'].search([('employee_id', '=', employee.id)])

        values = {
            'leave_records': leave_records,
        }
        return request.render('portal_attendance_artx_updated.portal_my_leaves', values)
    
    @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    def portal_leave_submit(self, **post):
        employee = request.env['hr.employee.public'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not employee:
            return request.redirect('/my/leave/new')  # Redirect to leave form on error
        
        leave_type = request.env['hr.leave.type'].sudo().search([('id', '=', int(post.get('leave_type')))], limit=1)
        if not leave_type:
            return request.redirect('/my/leave/new')

        start_date = post.get('start_date')
        end_date = post.get('end_date')

        if leave_type and start_date and end_date:
            request.env['hr.leave'].sudo().create({
                'employee_id': employee.id,
                'holiday_status_id': leave_type.id,
                'request_date_from': start_date,
                'request_date_to': end_date,
            })
            return request.redirect('/my/leaves')  # Redirect to leave requests
        return request.redirect('/my/leave/new')

    @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    def portal_leave_submit(self, **post):
        try:
            leave_type_id = int(post.get('leave_type', 0))  # Retrieve the leave type ID
            start_date = post.get('start_date')
            end_date = post.get('end_date')
            employee_id = request.env.user.employee_id.id


            # Validate the leave type
            leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)
            if not leave_type.exists():
                return request.redirect('/my/leave/new?error=invalid_leave_type')

            # Create the leave request
            if start_date and end_date:
                request.env['hr.leave'].sudo().create({
                    'employee_id': employee_id,
                    'holiday_status_id': leave_type_id,
                    'request_date_from': start_date,
                    'request_date_to': end_date,
                })
                return request.redirect('/my/leaves')  # Redirect to the user's leave requests
            else:
                return request.redirect('/my/leave/new?error=missing_dates')
        except Exception as e:
            return request.redirect(f'/my/leave/new?error={str(e)}')

    @http.route(['/my/leave/new'], type='http', auth='user', website=True)
    def portal_leave_form(self, **kwargs):
        leave_types = request.env['hr.leave.type'].sudo().search([])
        return request.render('portal_attendance_artx_updated.leave_form_template', {'leave_types': leave_types})

    # class PortalAttendance(http.Controller):
