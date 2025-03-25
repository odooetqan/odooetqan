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
    def portal_my_attendance(self, **kwargs):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
    
        if not employee:
            return request.redirect('/my/home')  # Redirect if no employee is found
    
        today = fields.Date.today()
        first_day_of_current_month = today.replace(day=1)
        fifteenth_previous_month = first_day_of_current_month - timedelta(days=15)
    
        # Get attendance records within the date range
        attendance_records = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', fifteenth_previous_month),
            ('check_in', '<=', today)
        ])
    

    
        # attendance_records = request.env['hr.attendance'].sudo().search_read([
        #     ('employee_id', '=', request.env.user.employee_id.id),
        #     ('check_in', '>=', fifteenth_previous_month),
        #     ('check_in', '<=', today)
        # ], ['check_in', 'check_out', 'worked_hours', 'overtime_minutes', 'lateness', 'deduction_amount'])


        # Convert check-in and check-out times from UTC to Asia/Riyadh
        user_tz = pytz.timezone('Asia/Riyadh')  # Set to Riyadh timezone
        utc_tz = pytz.UTC
    
        def convert_to_tz(dt):
            if dt:
                dt_utc = dt.replace(tzinfo=utc_tz) if dt.tzinfo is None else dt.astimezone(utc_tz)
                return dt_utc.astimezone(user_tz).replace(tzinfo=None)  # Convert to Riyadh and remove tzinfo
            return None
        
        def convert_datetime_to_str(dt):
            if dt:
                return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format datetime to string
            return None
    
        converted_attendance = []
        for record in attendance_records:
            converted_attendance.append({
                'id': record.id,
                'check_in': convert_datetime_to_str(convert_to_tz(record.check_in)),
                'check_out': convert_datetime_to_str(convert_to_tz(record.check_out)) if record.check_out else None,
                'worked_hours': record.worked_hours or 0.0,
                'lateness': record.lateness or 0.0,
                'overtime_minutes': record.overtime_minutes or 0.0,
                'deduction_amount': record.deduction_amount or 0.0,
            })

            # converted_attendance.append({
            #     'id': record.id,  # Add this line
            #     'check_in': convert_datetime_to_str(convert_to_tz(record.check_in)),
            #     'check_out': convert_datetime_to_str(convert_to_tz(record.check_out)) if record.check_out else None,
            #     # 'worked_hours': record.worked_hours,  # Keep `worked_hours` intact
            #     'worked_hours': record.worked_hours or 0.0,  # Keep `worked_hours` intact & Never NONE

            # })
    
        # Return JSON response
        # return json.dumps({
        #     'attendance_records': converted_attendance,
        # })
        

        # Define the values dictionary
        values = {
            'attendance_records': converted_attendance,
            'employee_name': employee.name,  # Add employee name for display
        }
        
        return request.render('portal_attendance_artx.portal_my_attendance', values)


# from odoo import http
# from odoo.http import request
# from datetime import datetime, timedelta
# from odoo import http, fields
# import json
# import logging
# import pytz

# _logger = logging.getLogger(__name__)


# class PortalAttendance(http.Controller):
#     @http.route(['/my/attendance'], type='http', auth='user', website=True)
#     def portal_my_attendance(self, **kwargs):
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
    
#         if not employee:
#             return request.redirect('/my/home')  # Redirect if no employee is found
    
#         today = fields.Date.today()
#         first_day_of_current_month = today.replace(day=1)
#         fifteenth_previous_month = first_day_of_current_month - timedelta(days=15)
    
#         # Get attendance records within the date range
#         attendance_records = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id),
#             ('check_in', '>=', fifteenth_previous_month),
#             ('check_in', '<=', today)
#         ])
    
#         # Convert check-in and check-out times from UTC to Asia/Riyadh
#         user_tz = pytz.timezone('Asia/Riyadh')  # Set to Riyadh timezone
#         utc_tz = pytz.UTC
    
#         def convert_to_tz(dt):
#             if dt:
#                 dt_utc = dt.replace(tzinfo=utc_tz) if dt.tzinfo is None else dt.astimezone(utc_tz)
#                 return dt_utc.astimezone(user_tz).replace(tzinfo=None)  # Convert to Riyadh and remove tzinfo
#             return None
        
#         def convert_datetime_to_str(dt):
#             if dt:
#                 return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format datetime to string
#             return None
    
#         converted_attendance = []
#         for record in attendance_records:
#             converted_attendance.append({
#                 'check_in': convert_datetime_to_str(convert_to_tz(record.check_in)),
#                 'check_out': convert_datetime_to_str(convert_to_tz(record.check_out)) if record.check_out else None,
#                 'worked_hours': record.worked_hours,  # Keep `worked_hours` intact
#             })
    
#         # Return JSON response
#         return json.dumps({
#             'attendance_records': converted_attendance,
#         })


    
    
    # @http.route(['/my/attendance'], type='http', auth='user', website=True)
    # def portal_my_attendance(self, **kwargs):
    #     """
    #     Display `hr.attendance` records converted from UTC to Asia/Riyadh timezone.
    #     """
    #     user = request.env.user
    #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        
    #     if not employee:
    #         return request.redirect('/my/home')  # Redirect if no employee is found

    #     today = fields.Date.today()
    #     first_day_of_current_month = today.replace(day=1)
    #     fifteenth_previous_month = first_day_of_current_month - timedelta(days=15)

    #     # Get attendance records within the date range
    #     attendance_records = request.env['hr.attendance'].sudo().search([
    #         ('employee_id', '=', employee.id),
    #         ('check_in', '>=', fifteenth_previous_month),
    #         ('check_in', '<=', today)
    #     ])

    #     # Convert check-in and check-out times from UTC to Asia/Riyadh
    #     user_tz = pytz.timezone('Asia/Riyadh')  # Set to Riyadh timezone
    #     utc_tz = pytz.UTC

    #     def convert_to_tz(dt):
    #         if dt:
    #             dt_utc = dt.replace(tzinfo=utc_tz) if dt.tzinfo is None else dt.astimezone(utc_tz)
    #             return dt_utc.astimezone(user_tz).replace(tzinfo=None)  # Convert to Riyadh and remove tzinfo
    #         return None

    #     converted_attendance = []
    #     for record in attendance_records:
    #         converted_attendance.append({
    #             'check_in': convert_to_tz(record.check_in),
    #             'check_out': convert_to_tz(record.check_out) if record.check_out else None,
    #             'worked_hours': record.worked_hours,  # Keep `worked_hours` intact
    #         })

    #     values = {
    #         'attendance_records': converted_attendance,
    #     }
    #     return request.render('portal_attendance_artx.portal_my_attendance', values)

# class PortalAttendance(http.Controller):

#     @http.route(['/my/attendance'], type='http', auth='user', website=True)
#     def portal_my_attendance(self, **kwargs):
#         """
#         Display `hr.attendance` records converted from UTC to Asia/Riyadh timezone.
#         """
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        
#         if not employee:
#             return request.redirect('/my/home')  # Redirect if no employee is found

#         today = fields.Date.today()
#         first_day_of_current_month = today.replace(day=1)
#         fifteenth_previous_month = first_day_of_current_month - timedelta(days=15)

#         # Get attendance records within the date range
#         attendance_records = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id),
#             ('check_in', '>=', fifteenth_previous_month),
#             ('check_in', '<=', today)
#         ])

#         # Convert check-in and check-out times from UTC to Asia/Riyadh
#         user_tz = pytz.timezone('Asia/Riyadh')  # Set to Riyadh timezone
#         utc_tz = pytz.UTC

#         def convert_to_tz(dt):
#             if dt:
#                 dt_utc = dt.replace(tzinfo=utc_tz) if dt.tzinfo is None else dt.astimezone(utc_tz)
#                 return dt_utc.astimezone(user_tz).replace(tzinfo=None)  # Convert to Riyadh and remove tzinfo
#             return None

#         converted_attendance = []
#         for record in attendance_records:
#             converted_attendance.append({
#                 'check_in': convert_to_tz(record.check_in),
#                 'check_out': convert_to_tz(record.check_out) if record.check_out else None,
#                 'worked_hours': record.worked_hours,
#             })

#         values = {
#             'attendance_records': converted_attendance,
#         }
#         return request.render('portal_attendance_artx.portal_my_attendance', values)


# class PortalAttendance(http.Controller):

#     @http.route(['/my/attendance'], type='http', auth='user', website=True)
#     def portal_my_attendance(self, **kwargs):
#         """
#         Display `hr.attendance` records converted from UTC to Asia/Riyadh timezone.
#         """
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        
#         if not employee:
#             return request.redirect('/my/home')  # Redirect if no employee is found

#         today = fields.Date.today()
#         first_day_of_current_month = today.replace(day=1)
#         fifteenth_previous_month = first_day_of_current_month - timedelta(days=15)

#         # Get attendance records within the date range
#         attendance_records = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id),
#             ('check_in', '>=', fifteenth_previous_month),
#             ('check_in', '<=', today)
#         ])

#         # Convert check-in and check-out times from UTC to Asia/Riyadh
#         user_tz = pytz.timezone('Asia/Riyadh')  # Set to Riyadh timezone
#         utc_tz = pytz.UTC

#         def convert_to_tz(dt):
#             if dt:
#                 dt_utc = dt.replace(tzinfo=utc_tz)
#                 return dt_utc.astimezone(user_tz)
#             return None

#         for record in attendance_records:
#             if record.check_in:
#                 record.check_in = convert_to_tz(record.check_in).replace(tzinfo=None)
#             if record.check_out:
#                 record.check_out = convert_to_tz(record.check_out).replace(tzinfo=None)

#         values = {
#             'attendance_records': attendance_records,  # Pass ORM objects
#         }
#         return request.render('portal_attendance_artx.portal_my_attendance', values)


# class PortalAttendance(http.Controller):

#     @http.route(['/my/attendance'], type='http', auth='user', website=True)
#     def portal_my_attendance(self, **kwargs):
#         """
#         Display `hr.attendance` records converted from UTC to Asia/Riyadh timezone.
#         """
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        
#         if not employee:
#             return request.redirect('/my/home')  # Redirect if no employee is found

#         today = fields.Date.today()
#         first_day_of_current_month = today.replace(day=1)
#         fifteenth_previous_month = first_day_of_current_month - timedelta(days=15)

#         # Get attendance records within the date range
#         attendance_records = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id),
#             ('check_in', '>=', fifteenth_previous_month),
#             ('check_in', '<=', today)
#         ])

#         # Convert check-in and check-out times from UTC to Asia/Riyadh
#         user_tz = pytz.timezone('Asia/Riyadh')  # Set to Riyadh timezone
#         utc_tz = pytz.UTC

#         def convert_to_tz(dt):
#             if dt:
#                 dt_utc = dt.replace(tzinfo=utc_tz)
#                 return dt_utc.astimezone(user_tz)
#             return None

#         converted_attendance = []
#         #for record in attendance_records:
                    
#             #record.check_in = convert_to_tz(record.check_in)
#             #record.check_out = convert_to_tz(record.check_out) if record.check_out else None
            
#             #converted_attendance.append({
#             #    'check_in': convert_to_tz(record.check_in),
#             #    'check_out': convert_to_tz(record.check_out) if record.check_out else None,
#              #   'worked_hours': record.worked_hours,
#            # })

#         for record in attendance_records:
#             record.check_in = convert_to_tz(record.check_in)
#             record.check_out = convert_to_tz(record.check_out) if record.check_out else None

#         values = {
#             'attendance_records': attendance_records,  # Pass ORM objects instead of dicts
#         }
#         return request.render('portal_attendance_artx.portal_my_attendance', values)

        
#        # values = {
#        #     'attendance_records': converted_attendance,
#       #  }
#       #  return request.render('portal_attendance_artx.portal_my_attendance', values)
# #_________________________________________________________________________________________________________________________________

# class PortalAttendance(http.Controller):

#     @http.route(['/my/attendance'], type='http', auth='user', website=True)
#     def portal_my_attendance(self, **kwargs):
#         """
#         Display `hr.attendance` records as they are, filtered from the 15th of the previous month to today.
#         """
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        
#         if not employee:
#             return request.redirect('/my/home')  # Redirect if no employee is found

#         # Get today's date
#         today = fields.Date.today()

#         # Get the 15th of the previous month
#         first_day_of_current_month = today.replace(day=1)
#         fifteenth_previous_month = first_day_of_current_month - timedelta(days=15)

#         # Get attendance records within the date range
#         attendance_records = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id),
#             ('check_in', '>=', fifteenth_previous_month),
#             ('check_in', '<=', today)
#         ])

#         values = {
#             'attendance_records': attendance_records,
#         }
#         return request.render('portal_attendance_artx.portal_my_attendance', values)

class AttendanceController(http.Controller):

    @http.route('/portal/add_attendance', type='http', auth="user", methods=['POST'], csrf=False)
    def add_attendance(self, **kwargs):
        """
        Allows adding a check-in. Does not allow check-outs.
        Disallows creating a check-in that is older than 30 days from now.
        """
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not employee:
            response_data = {'success': False, 'message': 'Employee not found for the logged-in user'}
            return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

        # Retrieve check_in from the POST data
        check_in_str = kwargs.get('check_in')
        if not check_in_str:
            response_data = {'success': False, 'message': 'No check_in date/time provided'}
            return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

        # Convert the check_in string to a datetime object
        try:
            check_in_dt = fields.Datetime.from_string(check_in_str)
        except Exception:
            check_in_dt = False

        if not check_in_dt:
            response_data = {'success': False, 'message': 'Invalid check_in format'}
            return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

        # Disallow check-in older than 30 days
        thirty_days_ago = fields.Datetime.now() - timedelta(days=30)
        if check_in_dt < thirty_days_ago:
            response_data = {'success': False, 'message': 'Cannot create attendance older than 30 days'}
            return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

        # Create new attendance record
        attendance = request.env['hr.attendance'].sudo().create({
            'employee_id': employee.id,
            'check_in': check_in_dt,
            # Note: No check_out is being set here
        })

        response_data = {'success': True, 'message': 'Check-in recorded'}
        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

# #________________________________________________________________________________________________________________________________

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
        return request.render('portal_attendance_artx.portal_my_leaves', values)
    

    @http.route(['/my/leave/new'], type='http', auth="user", website=True)
    def portal_leave_request_form(self, **kw):
        leave_types = request.env['hr.leave.type'].sudo().search([])
        return request.render('portal_attendance_artx.leave_form_template',{
            'leave_types': leave_types
        })
    
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

####################### End  portal Attendance ##########################################
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
