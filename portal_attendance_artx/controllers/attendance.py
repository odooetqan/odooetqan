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

        # Fetch attendance records
        attendance_records = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', fifteenth_previous_month),
            ('check_in', '<=', today)
        ])

        return request.render('portal_attendance_artx.portal_my_attendance', {
            'attendance_records': attendance_records  # Pass ORM records
        })

    # @http.route(['/my/attendance'], type='http', auth='user', website=True)
    # def portal_my_attendance(self, **kwargs):
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

    #     return request.render('portal_attendance_artx.portal_my_attendance', {
    #         'attendance_records': attendance_records
    #     })


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
    
    # @http.route(['/my/leave/new'], type='http', auth='user', website=True)
    # def portal_leave_form(self, **kwargs):
    #     # Fetch leave types from the database
    #     leave_types = request.env['hr.leave.type'].sudo().search([])
    #     return request.render('portal_attendance_artx.leave_form_template', {'leave_types': leave_types})
    
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

    @http.route(['/my/leave/new'], type='http', auth='user', website=True)
    def portal_leave_form(self, **kwargs):
        leave_types = request.env['hr.leave.type'].sudo().search([])
        return request.render('portal_attendance_artx.leave_form_template', {'leave_types': leave_types})

    # class PortalLeave(http.Controller):
    # @http.route(['/my/leave/new'], type='http', auth="user", website=True)
    # def portal_new_leave(self, **kw):

    #     leave_types = request.env['hr.leave.type'].sudo().search([])
    #     return request.render('portal_attendance_artx.portal_new_leave_form', {
    #         'leave_types': leave_types,
    #     })
            # return request.render('portal_attendance_artx.portal_new_leave_form', {})












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

# #________________________________________________________________________________________________________________________________

# ############### PORTAL request to correct hr attendance 
# class PortalAttendanceCorrection(http.Controller):

#     @http.route(['/portal/request_attendance_correction'], type='http', auth="user", methods=['POST'], csrf=False)
#     def submit_attendance_correction(self, **kwargs):
#         """Allow employees to submit a new attendance correction request."""
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#         if not employee:
#             return request.redirect('/my/home?error=no_employee')

#         check_in = kwargs.get('check_in')
#         check_out = kwargs.get('check_out')
#         note = kwargs.get('note')

#         # Log received data for debugging
#         _logger.info(f"Received data: check_in={check_in}, check_out={check_out}, note={note}")

#         if not check_in or not check_out:
#             return request.redirect('/my/home?error=missing_fields')

#         try:
#             # Try Odoo's default datetime conversion
#             check_in_dt = fields.Datetime.to_datetime(check_in)
#             check_out_dt = fields.Datetime.to_datetime(check_out)

#         except Exception:
#             try:
#                 # Try converting HTML datetime-local format
#                 check_in_dt = datetime.strptime(check_in, '%Y-%m-%dT%H:%M')
#                 check_out_dt = datetime.strptime(check_out, '%Y-%m-%dT%H:%M')
#             except Exception as e:
#                 _logger.error(f"Datetime conversion error: {e}")
#                 return request.redirect('/my/home?error=datetime_format')

#         if check_in_dt >= check_out_dt:
#             return request.redirect('/my/home?error=invalid_time')

#         try:
#             correction_request = request.env['hr.attendance.correction'].sudo().create({
#                 'employee_id': employee.id,
#                 'check_in': check_in_dt,
#                 'check_out': check_out_dt,
#                 'note': note,
#                 'state': 'draft',
#             })
#             correction_request.message_post(
#                 body=f"New Attendance Correction Request from {employee.name}.",
#                 subtype_xmlid="mail.mt_comment"
#             )

#             if correction_request:
#                 return request.redirect('/my/home?success=request_created')
#             else:
#                 return request.redirect('/my/home?error=creation_failed')

#         except Exception as e:
#             _logger.error(f"Error creating attendance correction: {e}")
#             return request.redirect(f'/my/home?error={str(e)}')


#     # @http.route(['/portal/request_attendance_correction'], type='http', auth="user", methods=['POST'], csrf=False)
#     # def submit_attendance_correction(self, **kwargs):
#     #     """Allow employees to submit a new attendance correction request."""
#     #     user = request.env.user
#     #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#     #     if not employee:
#     #         return request.redirect('/my/home?error=no_employee')

#     #     check_in = kwargs.get('check_in')
#     #     check_out = kwargs.get('check_out')
#     #     note = kwargs.get('note')

#     #     # Log received data for debugging
#     #     _logger.info(f"Received data: check_in={check_in}, check_out={check_out}, note={note}")

#     #     if not check_in or not check_out:
#     #         return request.redirect('/my/attendance_correction?error=missing_fields')

#     #     try:
#     #         # Auto-convert datetime format
#     #         check_in_dt = fields.Datetime.to_datetime(check_in)
#     #         check_out_dt = fields.Datetime.to_datetime(check_out)

#     #         if check_in_dt >= check_out_dt:
#     #             return request.redirect('/my/attendance_correction?error=invalid_time')

#     #     except Exception as e:
#     #         _logger.error(f"Datetime conversion error: {e}")
#     #         return request.redirect('/my/attendance_correction?error=datetime_format')

#     #     try:
#     #         correction_request = request.env['hr.attendance.correction'].sudo().create({
#     #             'employee_id': employee.id,
#     #             'check_in': check_in_dt,
#     #             'check_out': check_out_dt,
#     #             'note': note,
#     #             'state': 'draft',
#     #         })

#     #         if correction_request:
#     #             return request.redirect('/my/attendance_correction?success=request_created')
#     #         else:
#     #             return request.redirect('/my/attendance_correction?error=creation_failed')

#     #     except Exception as e:
#     #         _logger.error(f"Error creating attendance correction: {e}")
#     #         return request.redirect(f'/my/attendance_correction?error={str(e)}')

# # class PortalAttendanceCorrection(http.Controller):
# #     @http.route(['/portal/request_attendance_correction'], type='http', auth="user", methods=['POST'], csrf=False)
# #     def submit_attendance_correction(self, **kwargs):
# #         """Allow employees to submit a new attendance correction request."""
# #         user = request.env.user
# #         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

# #         if not employee:
# #             return request.redirect('/my/home?error=no_employee')

# #         check_in = kwargs.get('check_in')
# #         check_out = kwargs.get('check_out')
# #         note = kwargs.get('note')

# #         # Log received data for debugging
# #         _logger.info(f"Received data: check_in={check_in}, check_out={check_out}, note={note}")

# #         if not check_in or not check_out:
# #             return request.redirect('/my/attendance_correction?error=missing_fields')

# #         try:
# #             # Auto-convert datetime format
# #             check_in_dt = fields.Datetime.to_datetime(check_in)
# #             check_out_dt = fields.Datetime.to_datetime(check_out)

# #             if check_in_dt >= check_out_dt:
# #                 return request.redirect('/my/attendance_correction?error=invalid_time')

# #         except Exception as e:
# #             _logger.error(f"Datetime conversion error: {e}")
# #             return request.redirect('/my/attendance_correction?error=datetime_format')

# #         try:
# #             correction_request = request.env['hr.attendance.correction'].sudo().create({
# #                 'employee_id': employee.id,
# #                 'check_in': check_in_dt,
# #                 'check_out': check_out_dt,
# #                 'note': note,
# #                 'state': 'draft',
# #             })

# #             if correction_request:
# #                 return request.redirect('/my/attendance_correction?success=request_created')
# #             else:
# #                 return request.redirect('/my/attendance_correction?error=creation_failed')

# #         except Exception as e:
# #             _logger.error(f"Error creating attendance correction: {e}")
# #             return request.redirect(f'/my/attendance_correction?error={str(e)}')

#     # @http.route(['/portal/request_attendance_correction'], type='http', auth="user", methods=['POST'], csrf=False)
#     # def submit_attendance_correction(self, **kwargs):
#     #     """Allow employees to submit a new attendance correction request."""
#     #     user = request.env.user
#     #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#     #     if not employee:
#     #         return request.redirect('/my/home?error=no_employee')

#     #     check_in = kwargs.get('check_in')
#     #     check_out = kwargs.get('check_out')
#     #     note = kwargs.get('note')

#     #     if not check_in or not check_out:
#     #         return request.redirect('/my/attendance_correction?error=missing_fields')

#     #     try:
#     #         check_in_dt = fields.Datetime.to_datetime(check_in)
#     #         check_out_dt = fields.Datetime.to_datetime(check_out)

#     #         if check_in_dt >= check_out_dt:
#     #             return request.redirect('/my/attendance_correction?error=invalid_time')
        
#     #     except Exception:
#     #         return request.redirect('/my/attendance_correction?error=datetime_format')

#     #     try:
#     #         correction_request = request.env['hr.attendance.correction'].sudo().create({
#     #             'employee_id': employee.id,
#     #             'check_in': check_in_dt,
#     #             'check_out': check_out_dt,
#     #             'note': note,
#     #             'state': 'draft',
#     #         })

#     #         if correction_request:
#     #             return request.redirect('/my/attendance_correction?success=request_created')
#     #         else:
#     #             return request.redirect('/my/attendance_correction?error=creation_failed')

#     #     except Exception as e:
#     #         return request.redirect(f'/my/attendance_correction?error={str(e)}')


#     # @http.route(['/my/attendance_correction'], type='http', auth='user', website=True)
#     # def portal_my_attendance_correction(self, **kwargs):
#     #     """ Display all correction requests for the logged-in employee. """
#     #     user = request.env.user
#     #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#     #     if not employee:
#     #         return request.redirect('/my/home')

#     #     correction_requests = request.env['hr.attendance.correction'].sudo().search([
#     #         ('employee_id', '=', employee.id)
#     #     ])

#     #     values = {
#     #         'correction_requests': correction_requests,
#     #     }
#     #     return request.render('portal_attendance_artx.portal_my_attendance_correction', values)

#     # @http.route(['/portal/request_attendance_correction'], type='http', auth="user", methods=['POST'], csrf=False)
#     # def submit_attendance_correction(self, **kwargs):
#     #     user = request.env.user
#     #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
    
#     #     if not employee:
#     #         return request.redirect('/my/home')
    
#     #     check_in = kwargs.get('check_in')
#     #     check_out = kwargs.get('check_out')
#     #     note = kwargs.get('note')
    
#     #     try:
#     #         check_in_dt = fields.Datetime.to_datetime(check_in) if check_in else False
#     #         check_out_dt = fields.Datetime.to_datetime(check_out) if check_out else False
#     #     except Exception as e:
#     #         return request.redirect('/my/attendance_correction?error=datetime_format')
    
#     #     request.env['hr.attendance.correction'].sudo().create({
#     #         'employee_id': employee.id,
#     #         'check_in': check_in_dt,
#     #         'check_out': check_out_dt,
#     #         'note': note,
#     #         'state': 'draft',
#     #     })
    
#     #     return request.redirect('/my/attendance_correction')

#     # @http.route(['/portal/request_attendance_correction'], type='http', auth="user", methods=['POST'], csrf=False)
#     # def submit_attendance_correction(self, **kwargs):
#     #     """ Allow employees to submit a new attendance correction request. """
#     #     user = request.env.user
#     #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#     #     if not employee:
#     #         return request.redirect('/my/home')

#     #     check_in = kwargs.get('check_in')
#     #     check_out = kwargs.get('check_out')
#     #     note = kwargs.get('note')

#     #     request.env['hr.attendance.correction'].sudo().create({
#     #         'employee_id': employee.id,
#     #         'check_in': check_in,
#     #         'check_out': check_out,
#     #         'note': note,
#     #         'state': 'draft',
#     #     })

#     #     return request.redirect('/my/attendance_correction')

# ########################End POrtal Request ########################################################################################
# # class PortalAttendance(http.Controller):

# #     @http.route(['/my/attendance'], type='http', auth='user', website=True)
# #     def portal_my_attendance(self, **kwargs):
# #         """
# #         Show attendance records for the current user (employee) from the last 30 days only.
# #         """
# #         user = request.env.user
# #         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
# #         if not employee:
# #             # Optionally redirect or show an error if no employee is linked to this user
# #             return request.redirect('/my/home')  

# #         thirty_days_ago = fields.Datetime.now() - timedelta(days=30)
# #         attendance_records = request.env['hr.attendance'].sudo().search([
# #             ('employee_id', '=', employee.id),
# #             ('check_in', '>=', thirty_days_ago)
# #         ])

# #         values = {
# #             'attendance_records': attendance_records,
# #         }
# #         # Adjust the template name to match your actual template
# #         return request.render('portal_attendance_artx.portal_my_attendance', values)

# #---- TO addd tree attendance  portal gate#######################################################################################################################


# # class PortalAttendance(http.Controller):
#     # @http.route(['/my/attendance'], type='http', auth="user", website=True)
#     # def portal_attendance(self, **kwargs):
#     #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
#     #     attendance_records = request.env['hr.attendance'].sudo().search([('employee_id', '=', employee.id)])
#     #     values = {
#     #         'attendance_records': attendance_records,
#     #     }
#     #     return request.render('portal_attendance_artx.portal_attendance_tree', values)
# #---- TO addd tree attendance  portal gate
# # from odoo import http
# # from odoo.http import request

# class PortalAttendance(http.Controller):
#     @http.route(['/my/attendance'], type='http', auth='user', website=True)
#     def portal_my_attendance(self, **kwargs):
#         attendance_records = request.env['hr.attendance'].sudo().search([
#             ('employee_id.user_id', '=', request.env.user.id)
#         ])
#         values = {
#             'attendance_records': attendance_records
#         }
#         # return request.render('portal_attendance_artx_name.portal_my_attendance', values)
#         return request.render('portal_attendance_artx.portal_my_attendance', values)

        
# #---- TO addd tree attendance  portal gate 2222222222222222




# class AttendanceController(http.Controller):

#     @http.route('/portal/add_attendance', type='http', auth="user", methods=['POST'], csrf=False)
#     def add_attendance(self, **kwargs):
#         # Get the current logged-in user
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#         if not employee:
#             response_data = {'success': False, 'message': 'Employee not found for the logged-in user'}
#             return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

#         check_in = kwargs.get('check_in')
#         check_out = kwargs.get('check_out')

#         if check_in:
#             # Handle check-in logic
#             attendance = request.env['hr.attendance'].sudo().create({
#                 'check_in': check_in,
#                 'employee_id': employee.id,
#             })
#             response_data = {'success': True, 'message': 'Check-in recorded'}

#         elif check_out:
#             # Handle check-out logic (find the latest check-in and update the record)
#             attendance = request.env['hr.attendance'].sudo().search([
#                 ('employee_id', '=', employee.id),
#                 ('check_out', '=', False)
#             ], limit=1)

#             if attendance:
#                 attendance.sudo().write({'check_out': check_out})
#                 response_data = {'success': True, 'message': 'Check-out recorded'}
#             else:
#                 response_data = {'success': False, 'message': 'No check-in found to check out from'}

#         return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

#     @http.route('/portal/get_attendance_status', type='http', auth="user", methods=['GET'], csrf=False)
#     def get_attendance_status(self, **kwargs):
#         # Fetch the currently logged-in user
#         user = request.env.user
#         print('Logged-in user:', user.name, user.id)

#         # Fetch the employee associated with the user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
#         if not employee:
#             print('No employee found for user:', user.id)
#             response_data = {
#                 'success': False,
#                 'message': 'No employee associated with this user.'
#             }
#             return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

#         print('Employee found:', employee.name, employee.id)

#         # Search for attendance records where the user is checked in (check_out is False)
#         attendance = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id),
#             ('check_out', '=', False)
#         ], limit=1)

#         if attendance:
#             check_in_time = attendance.check_in
#             print('Attendance record found with check-in:', check_in_time)
#             response_data = {
#                 'success': True,
#                 'message': 'Currently checked in',
#                 'check_in': check_in_time.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
#             }
#         else:
#             print('No active attendance (checked in) record found.')
#             response_data = {
#                 'success': True,
#                 'message': 'Currently checked out',
#             }

#         return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])
    
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


# class PortalAttendance(http.Controller):

#     @http.route('/portal/add_attendance', type='json', auth='user', methods=['POST'])
#     def add_attendance(self, **kwargs):
#         user = request.env.user
#         employee = user.employee_id

#         if not employee:
#             return {'error': 'الموظف غير موجود'}

#         # البحث عن آخر تسجيل حضور
#         last_attendance = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id)
#         ], order="check_in desc", limit=1)

#         if last_attendance and not last_attendance.check_out:
#             return {'error': 'يجب تسجيل الخروج قبل تسجيل حضور جديد'}

#         try:
#             # إنشاء الحضور
#             attendance = request.env['hr.attendance'].sudo().create({
#                 'employee_id': employee.id,
#                 'check_in': fields.Datetime.now(),
#             })

#             # تحديث بيانات الموظف
#             employee.sudo().write({
#                 'last_attendance_id': attendance.id,
#                 'last_check_in': attendance.check_in,
#             })

#             return {'success': True, 'attendance_id': attendance.id}

#         except Exception as e:
#             return {'error': f'خطأ أثناء إنشاء الحضور: {str(e)}'}




# # class AttendanceController(http.Controller):

# #     @http.route('/portal/add_attendance', type='http', auth="user", methods=['POST'], csrf=False)
# #     def add_attendance(self, **kwargs):
# #         """
# #         Allows adding a check-in. Does not allow check-outs.
# #         Disallows creating a check-in that is older than 30 days from now.
# #         """
# #         user = request.env.user
# #         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

# #         if not employee:
# #             response_data = {'success': False, 'message': 'Employee not found for the logged-in user'}
# #             return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

# #         # Retrieve check_in from the POST data
# #         check_in_str = kwargs.get('check_in')
# #         if not check_in_str:
# #             response_data = {'success': False, 'message': 'No check_in date/time provided'}
# #             return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

# #         # Convert the check_in string to a datetime object
# #         try:
# #             check_in_dt = fields.Datetime.from_string(check_in_str)
# #         except Exception:
# #             check_in_dt = False

# #         if not check_in_dt:
# #             response_data = {'success': False, 'message': 'Invalid check_in format'}
# #             return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

# #         # Disallow check-in older than 30 days
# #         thirty_days_ago = fields.Datetime.now() - timedelta(days=30)
# #         if check_in_dt < thirty_days_ago:
# #             response_data = {'success': False, 'message': 'Cannot create attendance older than 30 days'}
# #             return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

# #         # Create new attendance record
# #         attendance = request.env['hr.attendance'].sudo().create({
# #             'employee_id': employee.id,
# #             'check_in': check_in_dt,
# #             # Note: No check_out is being set here
# #         })

# #         response_data = {'success': True, 'message': 'Check-in recorded'}
# #         return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])


    
#         # attendance_records = request.env['hr.attendance'].sudo().search_read([
#         #     ('employee_id', '=', request.env.user.employee_id.id),
#         #     ('check_in', '>=', fifteenth_previous_month),
#         #     ('check_in', '<=', today)
#         # ], ['check_in', 'check_out', 'worked_hours', 'overtime_minutes', 'lateness', 'deduction_amount'])


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
#                 'id': record.id,  # Add this line
#                 'check_in': convert_datetime_to_str(convert_to_tz(record.check_in)),
#                 'check_out': convert_datetime_to_str(convert_to_tz(record.check_out)) if record.check_out else None,
#                 # 'worked_hours': record.worked_hours,  # Keep `worked_hours` intact
#                 'worked_hours': record.worked_hours or 0.0,  # Keep `worked_hours` intact & Never NONE

#             })
    
#         # Return JSON response
#         # return json.dumps({
#         #     'attendance_records': converted_attendance,
#         # })
        

#         # Define the values dictionary
#         values = {
#             'attendance_records': converted_attendance,
#             'employee_name': employee.name,  # Add employee name for display
#         }
        
#         return request.render('portal_attendance_artx.portal_my_attendance', values)

# class PortalAttendance(http.Controller):

#     @http.route('/portal/add_attendance', type='json', auth='user', methods=['POST'], csrf=False)
#     def add_attendance(self, **kwargs):
#         """ Handle Employee Check-in """
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#         if not employee:
#             return {'success': False, 'message': 'الموظف غير موجود'}

#         last_attendance = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id)
#         ], order="check_in desc", limit=1)

#         if last_attendance and not last_attendance.check_out:
#             return {'success': False, 'message': 'يجب تسجيل الخروج أولاً'}

#         attendance = request.env['hr.attendance'].sudo().create({
#             'employee_id': employee.id,
#             'check_in': fields.Datetime.now(),
#         })

#         return {'success': True, 'message': 'تم تسجيل الحضور بنجاح!'}

#     @http.route('/portal/check_out', type='json', auth='user', methods=['POST'], csrf=False)
#     def check_out(self, **kwargs):
#         """ Handle Employee Check-out """
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#         if not employee:
#             return {'success': False, 'message': 'الموظف غير موجود'}

#         last_attendance = request.env['hr.attendance'].sudo().search([
#             ('employee_id', '=', employee.id),
#             ('check_out', '=', False)
#         ], order="check_in desc", limit=1)

#         if not last_attendance:
#             return {'success': False, 'message': 'لا يوجد تسجيل دخول مفتوح'}

#         last_attendance.sudo().write({'check_out': fields.Datetime.now()})

#         return {'success': True, 'message': 'تم تسجيل الخروج بنجاح!'}

