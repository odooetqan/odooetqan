from odoo import http
from odoo.http import request
from datetime import datetime
import json

#---- TO addd tree attendance  portal gate
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class PortalAttendance(http.Controller):
    @http.route(['/my/attendance'], type='http', auth='user', website=True)
    def portal_my_attendance(self, **kwargs):
        attendance_records = request.env['hr.attendance'].sudo().search([
            ('employee_id.user_id', '=', request.env.user.id)
        ])
        values = {
            'attendance_records': attendance_records
        }
        # return request.render('your_module_name.portal_my_attendance', values)
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

class PortalLeaves(http.Controller):

    @http.route('/my/leaves', type='http', auth='user', website=True)
    def portal_my_leaves(self, **kwargs):
        # Fetch leave requests for the logged-in user
        employee = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)], limit=1)
        leave_records = request.env['hr.leave'].search([('employee_id', '=', employee.id)])
        
        # Add logging here where it is contextually appropriate
        # _logger.info(f"Employee: {employee.name}, Leave Records: {leave_records.mapped('holiday_status_id.name')}")
        
        values = {
            'leave_records': leave_records,
        }
        return request.render('portal_attendance_artx.portal_my_leaves', values)

    @http.route(['/my/leave/new'], type='http', auth="user", website=True)
    def portal_new_leave(self, **kw):
        leave_types = request.env['hr.leave.type'].sudo().search([])
        # Log the leave types for debugging
        # request.env['ir.logging'].sudo().create({
        #     'name': 'Portal Leave Types Debug',
        #     'type': 'server',
        #     'level': 'info',
        #     'message': f"Leave Types: {leave_types.mapped('name')}",
        #     'path': 'portal.leave',  # تحديد مسار منطقي للسجل
        # })
        # request.env['ir.logging'].sudo().create({
        #     'name': 'Portal Leave Types Debug',
        #     'type': 'server',
        #     'level': 'info',
        #     'message': f"Leave Types: {leave_types.mapped('name')}",
        #     'path': 'portal.leave',  # تحديد مسار منطقي للسجل

        # })
        return request.render('portal_attendance_artx.portal_new_leave_form', {
            'leave_types': leave_types,
        })
    
    @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    def portal_leave_submit(self, **post):
        leave_type_id = int(post.get('leave_type', 0))
        start_date = post.get('start_date')
        end_date = post.get('end_date')
        employee_id = request.env.user.employee_id.id

        if leave_type_id and start_date and end_date:
            request.env['hr.leave'].sudo().create({
                'employee_id': employee_id,
                'holiday_status_id': leave_type_id,
                'request_date_from': start_date,
                'request_date_to': end_date,
            })
            return request.redirect('/my/leave')  # Redirect to the user's leave requests
        else:
            return request.redirect('/my/leave/new')  # Redirect back to the form on error
        

        
    # @http.route('/my/leaves', type='http', auth='user', website=True)
    # def portal_my_leaves(self, **kwargs):
    #     # Fetch leave requests for the logged-in user
    #     employee = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)], limit=1)
    #     leave_records = request.env['hr.leave'].search([('employee_id', '=', employee.id)])

    #     values = {
    #         'leave_records': leave_records,
    #     }
    #     return request.render('portal_attendance_artx.portal_my_leaves', values)
 


# class PortalLeave(http.Controller):
    # @http.route(['/my/leave/new'], type='http', auth="user", website=True)
    # def portal_new_leave(self, **kw):

    #     leave_types = request.env['hr.leave.type'].sudo().search([])
    #     return request.render('portal_attendance_artx.portal_new_leave_form', {
    #         'leave_types': leave_types,
    #     })

    # @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
    # def portal_leave_submit(self, **post):
    #     leave_type_id = int(post.get('leave_type', 0))
    #     start_date = post.get('start_date')
    #     end_date = post.get('end_date')
    #     employee_id = request.env.user.employee_id.id

    #     if leave_type_id and start_date and end_date:
    #         request.env['hr.leave'].sudo().create({
    #             'employee_id': employee_id,
    #             'holiday_status_id': leave_type_id,
    #             'request_date_from': start_date,
    #             'request_date_to': end_date,
    #         })
    #         return request.redirect('/my/leaves')  # Redirect to the leave requests list
    #     else:
    #         return request.redirect('/my/leave/new')  # Redirect back to the form on error

# class PortalLeave(http.Controller):


# # class PortalLeave(http.Controller):
#     @http.route(['/my/leave/submit'], type='http', auth='user', methods=['POST'], website=True)
#     def portal_leave_submit(self, **post):
#         leave_type_id = int(post.get('leave_type', 0))
#         start_date = post.get('start_date')
#         end_date = post.get('end_date')
#         employee_id = request.env.user.employee_id.id

#         if leave_type_id and start_date and end_date:
#             request.env['hr.leave'].sudo().create({
#                 'employee_id': employee_id,
#                 'holiday_status_id': leave_type_id,
#                 'request_date_from': start_date,
#                 'request_date_to': end_date,
#             })
#             return request.redirect('/my/leave')  # Redirect to the user's leave requests
#         else:
#             return request.redirect('/my/leave/new')  # Redirect back to the form on error

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

 
# # class PortalLeave(http.Controller):
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
    # class PortalAttendance(http.Controller):
    # @http.route(['/my/attendance'], type='http', auth="user", website=True)
    # def portal_attendance(self, **kwargs):
    #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
    #     attendance_records = request.env['hr.attendance'].sudo().search([('employee_id', '=', employee.id)])
    #     values = {
    #         'attendance_records': attendance_records,
    #     }
    #     return request.render('your_module.portal_attendance_tree', values)
#---- TO addd tree attendance  portal gate
# from odoo import http
# from odoo.http import request