# -*- coding: utf-8 -*-
# Copyright 2019 Artem Shurshilov
# Odoo Proprietary License v1.0

# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).

# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).

# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.

# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from odoo import models, fields, api, exceptions, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"
# class HrEmployee(models.AbstractModel):
#     _inherit = "hr.employee.base"
    #_description = "Employee"

    # def name_get(self):
    #     result = []
    #     for emp in self:
    #         result.append((emp.id, _("%(name)s [department=%(department)s,ID=%(identification_id)s]") % {
    #             'name': emp.name,
    #             'department': emp.department_id.name,
    #             'identification_id': emp.identification_id if emp.identification_id else 'not set',
    #         }))
    #     return result

    def parse_param(self, vals, mode='in'):
        if self._context.get('ismobile', None):
            vals.update({'ismobile_check_' + mode: self._context.get('ismobile', None)})
        if self._context.get('geospatial_id', None):
            vals.update({'geospatial_check_' + mode + '_id': self._context.get('geospatial_id', None)})
        if self._context.get('ip_id', None):
            vals.update({'ip_check_' + mode + '_id': self._context.get('ip_id', None)})
        if self._context.get('ip', None):
            vals.update({'ip_check_' + mode: self._context.get('ip', None)})
        if self._context.get('geo', None):
            vals.update({'geo_check_' + mode: self._context.get('geo', None)})
        if self._context.get('token', None):
            vals.update({'token_check_' + mode + '_id': self._context.get('token', None)})
        if self._context.get('webcam', None):
            vals.update({'webcam_check_' + mode: self._context.get('webcam', None)})
        if self._context.get('user_agent_html', None):
            vals.update({'user_agent_html_check_' + mode: self._context.get('user_agent_html', None)})
        if self._context.get('face_recognition_image', None):
            vals.update({'face_recognition_image_check_' + mode: self._context.get('face_recognition_image', None)})
        if self._context.get('kiosk_shop_id', None):
            vals.update({'kiosk_shop_id_check_' + mode: self._context.get('kiosk_shop_id', None)})

        access_allowed = self._context.get('access_allowed', None)
        access_denied = self._context.get('access_denied', None)
        access_allowed_disable = self._context.get('access_allowed_disable', None)
        access_denied_disable = self._context.get('access_denied_disable', None)
        accesses = self._context.get('accesses', None)
        if accesses:
            for key, value in accesses.items():
                if value.get('enable', False):
                    if value.get('access', False):
                        vals.update({key + '_check_' + mode: access_allowed})
                    else:
                        vals.update({key + '_check_' + mode: access_denied})
                else:
                    if value.get('access', False):
                        vals.update({key + '_check_' + mode: access_allowed_disable})
                    else:
                        vals.update({key + '_check_' + mode: access_denied_disable})

    def _attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = fields.Datetime.now()

        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            self.parse_param(vals)
            return self.env['hr.attendance'].create(vals)
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        if attendance:
            vals = {
                    'check_out': action_date,
                }
            self.parse_param(vals, 'out')
            attendance.write(vals)
        else:
            raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.sudo().name, })
        return attendance
