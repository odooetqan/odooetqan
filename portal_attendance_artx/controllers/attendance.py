from odoo import http
from odoo.http import request
from datetime import datetime
import json

#---- TO addd tree attendance  portal gate
from odoo import http
from odoo.http import request

# class PortalAttendance(http.Controller):
    # @http.route(['/my/attendance'], type='http', auth="user", website=True)
    # def portal_attendance(self, **kwargs):
    #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
    #     attendance_records = request.env['hr.attendance'].sudo().search([('employee_id', '=', employee.id)])
    #     values = {
    #         'attendance_records': attendance_records,
    #     }
    #     return request.render('portal_attendance_artx.portal_attendance_tree', values)
#---- TO addd tree attendance  portal gate
# from odoo import http
# from odoo.http import request

class PortalAttendance(http.Controller):
    @http.route(['/my/attendance'], type='http', auth='user', website=True)
    def portal_my_attendance(self, **kwargs):
        attendance_records = request.env['hr.attendance'].sudo().search([
            ('employee_id.user_id', '=', request.env.user.id)
        ])
        values = {
            'attendance_records': attendance_records
        }
        # return request.render('portal_attendance_artx_name.portal_my_attendance', values)
        return request.render('portal_attendance_artx.portal_my_attendance', values)

        
#---- TO addd tree attendance  portal gate 2222222222222222




class AttendanceController(http.Controller):

    @http.route('/portal/add_attendance', type='http', auth="user", methods=['POST'], csrf=False)
    def add_attendance(self, **kwargs):
        # Get the current logged-in user
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not employee:
            response_data = {'success': False, 'message': 'Employee not found for the logged-in user'}
            return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

        check_in = kwargs.get('check_in')
        check_out = kwargs.get('check_out')

        if check_in:
            # Handle check-in logic
            attendance = request.env['hr.attendance'].sudo().create({
                'check_in': check_in,
                'employee_id': employee.id,
            })
            response_data = {'success': True, 'message': 'Check-in recorded'}

        elif check_out:
            # Handle check-out logic (find the latest check-in and update the record)
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)

            if attendance:
                attendance.sudo().write({'check_out': check_out})
                response_data = {'success': True, 'message': 'Check-out recorded'}
            else:
                response_data = {'success': False, 'message': 'No check-in found to check out from'}

        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

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

# --- leaves 
# from odoo import http
# from odoo.http import request

class PortalLeaves(http.Controller):

    @http.route('/my/leaves', type='http', auth='user', website=True)
    def portal_my_leaves(self, **kwargs):
        # Fetch leave requests for the logged-in user
        employee = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)], limit=1)
        leave_records = request.env['hr.leave'].search([('employee_id', '=', employee.id)])

        values = {
            'leave_records': leave_records,
        }
        return request.render('portal_attendance_artx.portal_my_leaves', values)
    
    @http.route(['/my/leave/new'], type='http', auth='user', website=True)
    def portal_leave_form(self, **kwargs):
        # Fetch leave types from the database
        leave_types = request.env['hr.leave.type'].sudo().search([])
        return request.render('portal_attendance_artx.leave_form_template', {'leave_types': leave_types})
    
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











    # @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    # def portal_leave_submit(self, **post):
    #     try:
    #         leave_type_id = int(post.get('leave_type', 0))  # Retrieve the leave type ID
    #         start_date = post.get('start_date')
    #         end_date = post.get('end_date')
    #         employee_id = request.env.user.employee_id.id


    #         # Validate the leave type
    #         leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)
    #         if not leave_type.exists():
    #             return request.redirect('/my/leave/new?error=invalid_leave_type')

    #         # Create the leave request
    #         if start_date and end_date:
    #             request.env['hr.leave'].sudo().create({
    #                 'employee_id': employee_id,
    #                 'holiday_status_id': leave_type_id,
    #                 'request_date_from': start_date,
    #                 'request_date_to': end_date,
    #             })
    #             return request.redirect('/my/leaves')  # Redirect to the user's leave requests
    #         else:
    #             return request.redirect('/my/leave/new?error=missing_dates')
    #     except Exception as e:
    #         return request.redirect(f'/my/leave/new?error={str(e)}')

    # @http.route(['/my/leave/new'], type='http', auth='user', website=True)
    # def portal_leave_form(self, **kwargs):
    #     leave_types = request.env['hr.leave.type'].sudo().search([])
    #     return request.render('portal_attendance_artx.leave_form_template', {'leave_types': leave_types})

    # # class PortalLeave(http.Controller):
    #     @http.route(['/my/leave/new'], type='http', auth="user", website=True)
    #     def portal_new_leave(self, **kw):

    #         leave_types = request.env['hr.leave.type'].sudo().search([])
    #         return request.render('portal_attendance_artx.portal_new_leave_form', {
    #             'leave_types': leave_types,
    #         })
    #         # return request.render('portal_attendance_artx.portal_new_leave_form', {})
    
# class PortalLeave(http.Controller):
    # @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    # def portal_leave_submit(self, **post):
    #     leave_type_name = post.get('leave_type_name')  # Assuming the leave type is passed as a name
    #     start_date = post.get('start_date')
    #     end_date = post.get('end_date')
    #     employee_id = request.env.user.employee_id.id

    #     # Search for the leave type ID by name
    #     leave_type = request.env['hr.leave.type'].sudo().search([('name', '=', leave_type_name)], limit=1)
    #     leave_type_id = leave_type.id if leave_type else None

    #     if leave_type_id and start_date and end_date:
    #         request.env['hr.leave'].sudo().create({
    #             'employee_id': employee_id,
    #             'holiday_status_id': leave_type_id,
    #             'request_date_from': start_date,
    #             'request_date_to': end_date,
    #         })
    #         return request.redirect('/my/leaves')  # Redirect to the user's leave requests
    #     else:
    #         return request.redirect('/my/leave/new')  # Redirect back to the form on error


    # @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    # def portal_leave_submit(self, **post):
    #     leave_type_id = int(post.get('leave_type', 0))
    #     start_date = post.get('start_date')
    #     end_date = post.get('end_date')
    #     employee_id = request.env.user.employee_id.id

    #     if leave_type_id and start_date and end_date:
    #         request.env['hr.leave'].sudo().create({
    #             'employee_id': employee_id,
    #             'holiday_status_id': 1,
    #             'request_date_from': start_date,
    #             'request_date_to': end_date,
    #         })
    #         return request.redirect('/my/leaves')  # Redirect to the user's leave requests
    #     else:
    #         return request.redirect('/my/leave/new')  # Redirect back to the form on error

    # @http.route(['/my/leave/submit'], type='http', auth="user", methods=["POST"], website=True, csrf=True)
    # def portal_leave_submit(self, **post):
    #     user = request.env.user
    #     request.env['hr.leave'].sudo().create({
    #         'employee_id': user.employee_id.id,
    #         'leave_type': post.get('leave_type'),
    #         'start_date': post.get('start_date'),
    #         'end_date': post.get('end_date'),
    #         'state': 'draft',
    #     })
    #     return request.redirect('/my/leaves')

 
# class PortalLeave(http.Controller):
#     @http.route(['/my/leave/submit'], type='http', auth="user", methods=["POST"], website=True)
#     def portal_leave_submit(self, **post):
#         user = request.env.user
#         request.env['hr.leave'].sudo().create({
#             'employee_id': user.employee_id.id,
#             'leave_type': post.get('leave_type'),
#             'start_date': post.get('start_date'),
#             'end_date': post.get('end_date'),
#             'state': 'draft',
#         })
#         return request.redirect('/my/leaves')
# class PortalLeave(http.Controller):
    # @http.route(['/my/leave/new'], type='http', auth="user", website=True)
    # def portal_new_leave(self, **kw):
    #     return request.render('portal_attendance_artx.portal_new_leave_form', {})

 
# class PortalLeave(http.Controller):
    # @http.route(['/my/leave/submit'], type='http', auth="user", methods=["POST"], website=True)
    # def portal_leave_submit(self, **post):
    #     user = request.env.user
    #     request.env['hr.leave'].sudo().create({
    #         'employee_id': user.employee_id.id,
    #         'leave_type': post.get('leave_type'),
    #         'start_date': post.get('start_date'),
    #         'end_date': post.get('end_date'),
    #         'state': 'draft',
    #     })
    #     return request.redirect('/my/leaves')

    # @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    # def portal_leave_submit(self, **post):
    #     leave_type_id = int(post.get('leave_type', 0))  # Retrieve the leave type ID
    #     start_date = post.get('start_date')
    #     end_date = post.get('end_date')
    #     employee_id = request.env.user.employee_id.id

    #     # Validate the leave type
    #     leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)
    #     if not leave_type.exists():
    #         return request.redirect('/my/leave/new?error=invalid_leave_type')

    #     # Ensure all required fields are present
    #     if start_date and end_date:
    #         try:
    #             # Create the leave request
    #             request.env['hr.leave'].sudo().create({
    #                 'employee_id': employee_id,
    #                 'holiday_status_id': leave_type_id,
    #                 'request_date_from': start_date,
    #                 'request_date_to': end_date,
    #             })
    #             return request.redirect('/my/leaves')  # Redirect to the user's leave requests
    #         except Exception as e:
    #             # Handle any creation errors gracefully
    #             return request.redirect(f'/my/leave/new?error={str(e)}')
    #     else:
    #         return request.redirect('/my/leave/new?error=missing_dates')




    # @http.route('/portal/get_attendance_status', type='http', auth="none", methods=['GET'], csrf=False)
    # def get_attendance_status(self, **kwargs):
    #     # Simulate fetching data, including datetime objects
    #
    #     user = request.env.user
    #     print('user', user)
    #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
    #     print('employee', employee)
    #     attendance = request.env['hr.attendance'].sudo().search([
    #         ('employee_id', '=', employee.id),
    #         ('check_out', '=', False)
    #     ], limit=1)
    #     print('attendance', attendance)
    #
    #     if attendance:
    #         check_in_time = attendance.check_in
    #         response_data = {
    #             'success': True,
    #             'message': 'Currently checked in',
    #             'check_in': check_in_time.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
    #         }
    #     else:
    #         response_data = {
    #             'success': True,
    #             'message': 'Currently checked out',
    #         }
    #
    #     return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])