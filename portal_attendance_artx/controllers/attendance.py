# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime
import json

def _json(data, status=200):
    return request.make_response(
        json.dumps(data, default=str),
        headers=[('Content-Type', 'application/json')],
        status=status
    )

class AttendanceController(http.Controller):

    @http.route('/portal/add_attendance', type='http', auth='user', methods=['POST'], csrf=False)
    def add_attendance(self, **kw):
        """Create or close an attendance for the logged-in user.

        Body params (x-www-form-urlencoded or JSON):
          - action: 'check_in' | 'check_out'   (default: 'check_in')
          - lat: float (required)
          - lng: float (required)
          - at: ISO datetime string (optional; defaults to now server time)
        """
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return _json({'success': False, 'message': 'Employee not found for the logged-in user.'}, 404)

        action = (kw.get('action') or 'check_in').strip().lower()
        # allow both lat/lng and latitude/longitude names just in case
        lat = kw.get('lat') or kw.get('latitude')
        lng = kw.get('lng') or kw.get('longitude')
        ts  = kw.get('at')   # optional explicit datetime

        # strong validation up-front
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            return _json({'success': False, 'message': 'Missing or invalid lat/lng.'}, 400)

        # parse optional datetime
        explicit_dt = None
        if ts:
            try:
                # Accept common formats: 'YYYY-mm-dd HH:MM:SS' or ISO 'YYYY-mm-ddTHH:MM:SS'
                ts = ts.replace('T', ' ')
                explicit_dt = datetime.strptime(ts.split('.')[0], '%Y-%m-%d %H:%M:%S')
            except Exception:
                return _json({'success': False, 'message': 'Invalid datetime format in "at".'}, 400)

        Att = request.env['hr.attendance'].sudo()
        try:
            if action == 'check_out':
                # find the open attendance
                att = Att.search([('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1, order='check_in desc')
                if not att:
                    return _json({'success': False, 'message': 'No open check-in found for this employee.'}, 409)

                vals = {
                    'out_latitude': lat,
                    'out_longitude': lng,
                }
                if explicit_dt:
                    vals['check_out'] = explicit_dt
                att.write(vals)
                return _json({'success': True, 'message': 'Check-out recorded.', 'attendance_id': att.id})

            # default / explicit check-in
            vals = {
                'employee_id': employee.id,
                'in_latitude': lat,
                'in_longitude': lng,
            }
            if explicit_dt:
                vals['check_in'] = explicit_dt

            att = Att.create(vals)
            return _json({'success': True, 'message': 'Check-in recorded.', 'attendance_id': att.id})

        except Exception as e:
            # bubble up model/UserError messages as JSON with 400
            return _json({'success': False, 'message': str(e)}, 400)

    @http.route('/portal/get_attendance_status', type='http', auth='user', methods=['GET'], csrf=False)
    def get_attendance_status(self, **kw):
        """Return whether the logged-in user is currently checked in."""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return _json({'success': False, 'message': 'Employee not found for the logged-in user.'}, 404)

        att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1, order='check_in desc')

        if att:
            return _json({
                'success': True,
                'status': 'in',
                'check_in': att.check_in and att.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                'attendance_id': att.id,
            })
        return _json({'success': True, 'status': 'out'})
