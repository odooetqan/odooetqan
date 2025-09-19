# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import datetime
import json
import logging

_logger = logging.getLogger(__name__)


def _parse_dt(val):
    if not val:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val, fmt)
        except Exception:
            pass
    return None


class AttendanceController(http.Controller):

    @http.route('/portal/add_attendance', type='http', auth='user', methods=['POST'], csrf=False)
    def add_attendance(self, **kw):
        """Toggle attendance (check-in / check-out) for current user.
        Expects optional:
          - lat, lng (strings/floats) from browser geolocation
          - check_in / check_out (optional explicit timestamps)
        """
        user = request.env.user
        employee = user.employee_id or request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        def _json(resp, status=200):
            return request.make_response(json.dumps(resp), headers=[('Content-Type', 'application/json')], status=status)

        if not employee:
            return _json({'success': False, 'message': 'No employee linked to this user.'}, status=400)

        # Coordinates from the client (strings -> floats)
        lat = kw.get('lat')
        lng = kw.get('lng')
        try:
            lat = float(lat) if lat not in (None, '', 'null', 'undefined') else None
            lng = float(lng) if lng not in (None, '', 'null', 'undefined') else None
        except Exception:
            lat = lng = None

        # Many geo-enforcement addons read different context keys.
        geo_ctx = {
            # generic
            'lat': lat, 'lng': lng,
            # common variations
            'latitude': lat, 'longitude': lng,
            'attendance_latitude': lat, 'attendance_longitude': lng,
            'attendance_lat': lat, 'attendance_lng': lng,
            'portal_lat': lat, 'portal_lng': lng,
            # sometimes they read from ENV user context
            'user_latitude': lat, 'user_longitude': lng,
        }

        Att = request.env['hr.attendance'].sudo().with_context(**geo_ctx)

        explicit_check_in = _parse_dt(kw.get('check_in'))
        explicit_check_out = _parse_dt(kw.get('check_out'))
        now = fields.Datetime.now()

        try:
            if explicit_check_in and not explicit_check_out:
                rec = Att.create({'employee_id': employee.id, 'check_in': explicit_check_in})
                ts = explicit_check_in.strftime('%Y-%m-%d %H:%M:%S')
                return _json({'success': True, 'action': 'check_in', 'timestamp': ts, 'attendance_id': rec.id})

            if explicit_check_out and not explicit_check_in:
                open_att = Att.search([('employee_id', '=', employee.id), ('check_out', '=', False)], order='check_in desc', limit=1)
                if not open_att:
                    return _json({'success': False, 'message': 'No open attendance to check out from.'}, status=400)
                open_att.with_context(**geo_ctx).write({'check_out': explicit_check_out})
                ts = explicit_check_out.strftime('%Y-%m-%d %H:%M:%S')
                return _json({'success': True, 'action': 'check_out', 'timestamp': ts, 'attendance_id': open_att.id})

            # Default: toggle
            open_att = Att.search([('employee_id', '=', employee.id), ('check_out', '=', False)], order='check_in desc', limit=1)
            if open_att:
                open_att.with_context(**geo_ctx).write({'check_out': now})
                ts = now.strftime('%Y-%m-%d %H:%M:%S')
                return _json({'success': True, 'action': 'check_out', 'timestamp': ts, 'attendance_id': open_att.id})
            else:
                rec = Att.create({'employee_id': employee.id, 'check_in': now})
                ts = now.strftime('%Y-%m-%d %H:%M:%S')
                return _json({'success': True, 'action': 'check_in', 'timestamp': ts, 'attendance_id': rec.id})

        except Exception as e:
            _logger.exception("Portal add_attendance failed for employee %s", employee.id)
            # If your geo-enforcement raises UserError when lat/lng missing,
            # this makes the client see a clean JSON message.
            return _json({'success': False, 'message': str(e)}, status=400)

    @http.route('/portal/get_attendance_status', type='http', auth='user', methods=['GET'], csrf=False)
    def get_attendance_status(self, **kw):
        def _json(resp, status=200):
            return request.make_response(json.dumps(resp), headers=[('Content-Type', 'application/json')], status=status)

        user = request.env.user
        employee = user.employee_id or request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return _json({'success': False, 'message': 'No employee associated with this user.'}, status=400)

        Att = request.env['hr.attendance'].sudo()
        open_att = Att.search([('employee_id', '=', employee.id), ('check_out', '=', False)], order='check_in desc', limit=1)
        if open_att:
            return _json({
                'success': True,
                'status': 'in',
                'message': 'Currently checked in',
                'check_in': open_att.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                'attendance_id': open_att.id,
            })
        return _json({'success': True, 'status': 'out', 'message': 'Currently checked out'})
