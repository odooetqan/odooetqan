# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies
#    (https://www.cybrosys.com).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#

################################################################################
import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connecting the biometric device with Odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', required=True,
                            help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', required=True,
                                 help="The Port Number of the Device")
    address_id = fields.Many2one('res.partner', string='Working Address',
                                 help='Working address of the partner')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id.id,
                                 help='Current Company')

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception as e:
            _logger.error("Connection error: %s", e)
            return False

    def action_test_connection(self):
        """Checking the connection status"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                password=False, ommit_ping=False)
        try:
            if zk.connect():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Connected',
                        'type': 'success',
                        'sticky': False
                    }
                }
        except Exception as error:
            raise ValidationError(f'{error}')

    def action_set_timezone(self):
        """Function to set user's timezone to device"""
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0, force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                user_tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
                # Get current time in user's timezone and convert to device time
                user_timezone_time = pytz.utc.localize(fields.Datetime.now()).astimezone(pytz.timezone(user_tz))
                conn.set_time(user_timezone_time)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Set the Time',
                        'type': 'success',
                        'sticky': False
                    }
                }
            else:
                raise UserError(_("Please Check the Connection"))

    def action_clear_attendance(self):
        """Method to clear records from the zk.machine.attendance model and the device"""
        for info in self:
            try:
                machine_ip = info.device_ip
                zk_port = info.port_number
                try:
                    zk = ZK(machine_ip, port=zk_port, timeout=30,
                            password=0, force_udp=False, ommit_ping=False)
                except NameError:
                    raise UserError(_("Please install it with 'pip3 install pyzk'."))
                conn = self.device_connect(zk)
                if conn:
                    conn.enable_device()
                    clear_data = zk.get_attendance()
                    if clear_data:
                        # Clearing attendance data on the device
                        conn.clear_attendance()
                        # Clearing attendance log from Odoo (adjust table name if needed)
                        self._cr.execute("DELETE FROM zk_machine_attendance")
                        conn.disconnect()
                    else:
                        raise UserError(_('Unable to clear Attendance log. Are you sure the attendance log is not empty?'))
                else:
                    raise UserError(_('Unable to connect to Attendance Device. Please use Test Connection button to verify.'))
            except Exception as error:
                raise ValidationError(f'{error}')

    @api.model
    def cron_download(self):
        machines = self.search([])
        for machine in machines:
            machine.action_download_attendance()

    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                password=0, force_udp=False, ommit_ping=False)
        self.device_connect(zk).restart()

    def action_download_attendance(self):
        """Download attendance and store in an intermediate table before processing."""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance_obj = self.env['zk.machine.attendance']  # Intermediate table
        start_date = datetime(2023, 1, 1)  # ✅ Set the start date (January 1, 2024)

        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=15, password=0, force_udp=False, ommit_ping=False)
            except NameError:
                _logger.error("Pyzk module not found! Please install with 'pip3 install pyzk'.")
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

            conn = self.device_connect(zk)
            self.action_set_timezone()

            if conn:
                conn.disable_device()  # Disable device while fetching data
                users = conn.get_users()
                attendance_list = conn.get_attendance()

                _logger.info(f"✅ Total Attendance Data Retrieved: {len(attendance_list)} records.")

                filtered_attendance = []
                for each in attendance_list:
                    if each.timestamp >= start_date:
                        filtered_attendance.append(each)

                _logger.info(f"✅ Filtered Attendance Data: {len(filtered_attendance)} records (from {start_date})")

                if filtered_attendance:
                    for each in filtered_attendance:
                        _logger.info(f"🟡 User ID: {each.user_id}, Timestamp: {each.timestamp}, Punch Type: {each.punch}, Status: {each.status}")

                        # Convert timestamp to UTC
                        atten_time = each.timestamp
                        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        atten_time = fields.Datetime.to_string(utc_dt)

                        # Find the corresponding user
                        employee = self.env['hr.employee'].search([('device_id_num', '=', each.user_id)], limit=1)

                        if employee:
                            _logger.info(f"✅ Employee Found: {employee.name}, Device ID: {each.user_id}")

                            # Store attendance in the intermediate table
                            duplicate_atten = zk_attendance_obj.search([
                                ('device_id_num', '=', each.user_id),
                                ('punching_time', '=', atten_time)
                            ])

                            if not duplicate_atten:
                                zk_attendance_obj.create({
                                    'employee_id': employee.id,
                                    'device_id_num': each.user_id,
                                    'attendance_type': str(each.status),
                                    'punch_type': str(each.punch),
                                    'punching_time': atten_time,
                                    'address_id': info.address_id.id
                                })
                                _logger.info(f"✅ Attendance Record Created: Employee {employee.name}, Time {atten_time}")
                            else:
                                _logger.warning(f"⚠️ Duplicate Entry Skipped for {employee.name} at {atten_time}")

                        else:
                            _logger.warning(f"⚠️ No Employee Found for Device ID: {each.user_id}")

                else:
                    _logger.warning("⚠️ No attendance records found after 2024-01-01.")

                conn.disconnect()
                return True
            else:
                _logger.error("❌ Unable to connect, please check the network connections.")
                raise UserError(_('Unable to connect, please check the network connections.'))



    # def action_download_attendance(self):
    #     """Function to download attendance records from the device and update HR attendance"""
    #     _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
    #     zk_attendance_obj = self.env['zk.machine.attendance']
    #     hr_attendance_obj = self.env['hr.attendance']
    #     for info in self:
    #         machine_ip = info.device_ip
    #         zk_port = info.port_number
    #         try:
    #             zk = ZK(machine_ip, port=zk_port, timeout=15,
    #                     password=0, force_udp=False, ommit_ping=False)
    #         except NameError:
    #             raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
    #         conn = self.device_connect(zk)
    #         # Ensure the device time is set according to the user's timezone
    #         self.action_set_timezone()
    #         if conn:
    #             conn.disable_device()  # Disable device to avoid interference during download
    #             users = conn.get_users()
    #             attendance_list = conn.get_attendance()
    #             if attendance_list:
    #                 for each in attendance_list:
    #                     # Convert device timestamp to UTC
    #                     atten_time = each.timestamp
    #                     local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
    #                     local_dt = local_tz.localize(atten_time, is_dst=None)
    #                     utc_dt = local_dt.astimezone(pytz.utc)
    #                     utc_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
    #                     # Convert string back to datetime for Odoo
    #                     atten_time = fields.Datetime.to_string(datetime.datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S"))
                        
    #                     # Find the corresponding user info from the device
    #                     for uid in users:
    #                         if uid.user_id == each.user_id:
    #                             employee = self.env['hr.employee'].search([('device_id_num', '=', each.user_id)], limit=1)
    #                             if employee:
    #                                 # Create attendance log in the custom model if not duplicated
    #                                 duplicate_atten_ids = zk_attendance_obj.search([
    #                                     ('device_id_num', '=', each.user_id),
    #                                     ('punching_time', '=', atten_time)
    #                                 ])
    #                                 if not duplicate_atten_ids:
    #                                     zk_attendance_obj.create({
    #                                         'employee_id': employee.id,
    #                                         'device_id_num': each.user_id,
    #                                         'attendance_type': str(each.status),
    #                                         'punch_type': str(each.punch),
    #                                         'punching_time': atten_time,
    #                                         'address_id': info.address_id.id
    #                                     })
    #                                 # Process HR attendance: complete any open record or create a new one
    #                                 # Inside the loop where you process each attendance event
    #                                 #----------------------------------------------------------------------------------------------
    #                                 open_attendance = hr_attendance_obj.search([
    #                                     ('employee_id', '=', employee.id),
    #                                     ('check_out', '=', False)
    #                                 ], limit=1)

    #                                 if each.punch == 0:  # Check-In event
    #                                     if open_attendance:
    #                                         # Log a warning or update the open record's check_out, then optionally create a new record
    #                                         _logger.warning("Employee %s is already checked in. Completing the open record.", employee.name)
    #                                         # Complete the open record (update check_out) before starting a new session
    #                                         open_attendance.write({'check_out': atten_time})
    #                                         # Optionally, create a new record for the new check-in if your business process requires it:
    #                                         # hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})
    #                                     else:
    #                                         hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})
    #                                 elif each.punch == 1:  # Check-Out event
    #                                     if open_attendance:
    #                                         open_attendance.write({'check_out': atten_time})
    #                                     else:
    #                                         # Fallback: create a record with check_in and check_out equal to the event time
    #                                         hr_attendance_obj.create({
    #                                             'employee_id': employee.id,
    #                                             'check_in': atten_time,
    #                                             'check_out': atten_time
    #                                         })

    #                                 #----------------------------------------------------------------------------------------------


    #                                 open_attendance = hr_attendance_obj.search([
    #                                     ('employee_id', '=', employee.id),
    #                                     ('check_out', '=', False)
    #                                 ], limit=1)
    #                                 if each.punch == 0:  # Check-In event
    #                                     if open_attendance:
    #                                         # Complete the open attendance record by setting its check_out
    #                                         open_attendance.write({'check_out': atten_time})
    #                                         # Optionally, create a new record for the new check-in if needed:
    #                                         # hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})
    #                                     else:
    #                                         hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})
    #                                 elif each.punch == 1:  # Check-Out event
    #                                     if open_attendance:
    #                                         open_attendance.write({'check_out': atten_time})
    #                                     else:
    #                                         # No open record found; create a record with both check_in and check_out as fallback
    #                                         hr_attendance_obj.create({
    #                                             'employee_id': employee.id,
    #                                             'check_in': atten_time,
    #                                             'check_out': atten_time
    #                                         })
    #                             else:
    #                                 # If employee is not found, create a new employee record and corresponding attendance
    #                                 employee = self.env['hr.employee'].create({
    #                                     'device_id_num': each.user_id,
    #                                     'name': uid.name
    #                                 })
    #                                 zk_attendance_obj.create({
    #                                     'employee_id': employee.id,
    #                                     'device_id_num': each.user_id,
    #                                     'attendance_type': str(each.status),
    #                                     'punch_type': str(each.punch),
    #                                     'punching_time': atten_time,
    #                                     'address_id': info.address_id.id
    #                                 })
    #                                 hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})
    #                 conn.disconnect()
    #                 return True
    #             else:
    #                 raise UserError(_('Unable to get the attendance log, please try again later.'))
    #         else:
    #             raise UserError(_('Unable to connect, please check the parameters and network connections.'))


    # def action_download_attendance(self):
    #     """Download attendance and store in an intermediate table before processing."""
    #     _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
    #     zk_attendance_obj = self.env['zk.machine.attendance']  # Intermediate table
    #     for info in self:
    #         machine_ip = info.device_ip
    #         zk_port = info.port_number
    #         try:
    #             zk = ZK(machine_ip, port=zk_port, timeout=15, password=0, force_udp=False, ommit_ping=False)
    #         except NameError:
    #             raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

    #         conn = self.device_connect(zk)
    #         self.action_set_timezone()
    #         if conn:
    #             conn.disable_device()  # Disable device while fetching data
    #             users = conn.get_users()
    #             attendance_list = conn.get_attendance()
    #             if attendance_list:
    #                 for each in attendance_list:
    #                     # Convert timestamp to UTC
    #                     atten_time = each.timestamp
    #                     local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
    #                     local_dt = local_tz.localize(atten_time, is_dst=None)
    #                     utc_dt = local_dt.astimezone(pytz.utc)
    #                     atten_time = fields.Datetime.to_string(utc_dt)

    #                     # Find the corresponding user
    #                     employee = self.env['hr.employee'].search([('device_id_num', '=', each.user_id)], limit=1)
    #                     if employee:
    #                         # Store attendance in the intermediate table instead of `hr.attendance`
    #                         duplicate_atten = zk_attendance_obj.search([
    #                             ('device_id_num', '=', each.user_id),
    #                             ('punching_time', '=', atten_time)
    #                         ])
    #                         if not duplicate_atten:
    #                             zk_attendance_obj.create({
    #                                 'employee_id': employee.id,
    #                                 'device_id_num': each.user_id,
    #                                 'attendance_type': str(each.status),
    #                                 'punch_type': str(each.punch),
    #                                 'punching_time': atten_time,
    #                                 'address_id': info.address_id.id
    #                             })
    #             conn.disconnect()
    #             return True
    #         else:
    #             raise UserError(_('Unable to connect, please check the network connections.'))
    # def action_download_attendance(self):
    #     """Download attendance and store in an intermediate table before processing."""
    #     _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
    #     zk_attendance_obj = self.env['zk.machine.attendance']  # Intermediate table

    #     for info in self:
    #         machine_ip = info.device_ip
    #         zk_port = info.port_number
    #         try:
    #             zk = ZK(machine_ip, port=zk_port, timeout=15, password=0, force_udp=False, ommit_ping=False)
    #         except NameError:
    #             _logger.error("Pyzk module not found! Please install with 'pip3 install pyzk'.")
    #             raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

    #         conn = self.device_connect(zk)
    #         self.action_set_timezone()

    #         if conn:
    #             conn.disable_device()  # Disable device while fetching data
    #             users = conn.get_users()
    #             attendance_list = conn.get_attendance()

    #             _logger.info(f"Fetched {len(attendance_list)} attendance records from ZK machine.")

    #             if attendance_list:
    #                 for each in attendance_list:
    #                     _logger.info(f"Processing User ID: {each.user_id}, Punch Time: {each.timestamp}")

    #                     # Convert timestamp to UTC
    #                     atten_time = each.timestamp
    #                     local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
    #                     local_dt = local_tz.localize(atten_time, is_dst=None)
    #                     utc_dt = local_dt.astimezone(pytz.utc)
    #                     atten_time = fields.Datetime.to_string(utc_dt)

    #                     # Find the corresponding user
    #                     employee = self.env['hr.employee'].search([('device_id_num', '=', each.user_id)], limit=1)

    #                     if employee:
    #                         _logger.info(f"Employee Found: {employee.name}, Device ID: {each.user_id}")

    #                         # Store attendance in the intermediate table instead of `hr.attendance`
    #                         duplicate_atten = zk_attendance_obj.search([
    #                             ('device_id_num', '=', each.user_id),
    #                             ('punching_time', '=', atten_time)
    #                         ])

    #                         if not duplicate_atten:
    #                             zk_attendance_obj.create({
    #                                 'employee_id': employee.id,
    #                                 'device_id_num': each.user_id,
    #                                 'attendance_type': str(each.status),
    #                                 'punch_type': str(each.punch),
    #                                 'punching_time': atten_time,
    #                                 'address_id': info.address_id.id
    #                             })
    #                             _logger.info(f"Attendance Record Created: Employee {employee.name}, Time {atten_time}")
    #                         else:
    #                             _logger.warning(f"Duplicate Attendance Entry Skipped for {employee.name} at {atten_time}")
    #                     else:
    #                         _logger.warning(f"No employee found for Device ID: {each.user_id}")

    #             else:
    #                 _logger.warning("No attendance records fetched from the ZK machine.")

    #             conn.disconnect()
    #             return True
    #         else:
    #             _logger.error("Unable to connect, please check the network connections.")
    #             raise UserError(_('Unable to connect, please check the network connections.'))


class MachineAttendance(models.Model):
    """Intermediate table to store biometric attendance before processing."""
    _name = 'zk.machine.attendance'
    _description = 'Biometric Attendance Log'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    device_id_num = fields.Char(string="Device ID")
    attendance_type = fields.Selection([('0', 'Check In'), ('1', 'Check Out')], string="Attendance Type")
    punch_type = fields.Char(string="Punch Type")
    punching_time = fields.Datetime(string="Punching Time", required=True)
    address_id = fields.Many2one('res.partner', string="Location")
    processed = fields.Boolean(string="Processed", default=False)

    # @api.model
    def action_process_attendance(self):
        """Move validated attendance records from `zk.machine.attendance` to `hr.attendance`."""
        zk_attendance_obj = self.env['zk.machine.attendance']
        hr_attendance_obj = self.env['hr.attendance']

        unprocessed_attendance = zk_attendance_obj.search([('processed', '=', False)])
        for record in unprocessed_attendance:
            employee = record.employee_id
            atten_time = record.punching_time

            open_attendance = hr_attendance_obj.search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)

            if record.attendance_type == '0':  # Check-In
                if open_attendance:
                    # Close the previous open attendance before starting a new one
                    open_attendance.write({'check_out': atten_time})

                # Create a new Check-In record
                hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})

            elif record.attendance_type == '1':  # Check-Out
                if open_attendance:
                    open_attendance.write({'check_out': atten_time})
                else:
                    # If no Check-In exists, create a fallback record with both Check-In & Check-Out
                    hr_attendance_obj.create({
                        'employee_id': employee.id,
                        'check_in': atten_time,
                        'check_out': atten_time
                    })

            # ✅ Mark as processed so it's not duplicated next time
            record.write({'processed': True})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Attendance processed successfully!',
                'type': 'success',
                'sticky': False
            }
        }




# # -*- coding: utf-8 -*-
# ################################################################################
# #
# #    Cybrosys Technologies Pvt. Ltd.
# #
# #    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
# #    Author: Ammu Raj (odoo@cybrosys.com)
# #
# #    You can modify it under the terms of the GNU AFFERO
# #    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
# #
# #    This program is distributed in the hope that it will be useful,
# #    but WITHOUT ANY WARRANTY; without even the implied warranty of
# #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# #    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
# #
# #    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# #    (AGPL v3) along with this program.
# #    If not, see <http://www.gnu.org/licenses/>.
# #
# ################################################################################
# import datetime
# import logging
# import pytz
# from odoo import api, fields, models, _
# from odoo.exceptions import UserError, ValidationError

# _logger = logging.getLogger(__name__)
# try:
#     from zk import ZK, const
# except ImportError:
#     _logger.error("Please Install pyzk library.")


# class BiometricDeviceDetails(models.Model):
#     """Model for configuring and connect the biometric device with odoo"""
#     _name = 'biometric.device.details'
#     _description = 'Biometric Device Details'

#     name = fields.Char(string='Name', required=True, help='Record Name')
#     device_ip = fields.Char(string='Device IP', required=True,
#                             help='The IP address of the Device')
#     port_number = fields.Integer(string='Port Number', required=True,
#                                  help="The Port Number of the Device")
#     address_id = fields.Many2one('res.partner', string='Working Address',
#                                  help='Working address of the partner')
#     company_id = fields.Many2one('res.company', string='Company',
#                                  default=lambda
#                                      self: self.env.user.company_id.id,
#                                  help='Current Company')

#     def device_connect(self, zk):
#         """Function for connecting the device with Odoo"""
#         try:
#             conn = zk.connect()
#             return conn
#         except Exception:
#             return False

#     def action_test_connection(self):
#         """Checking the connection status"""
#         zk = ZK(self.device_ip, port=self.port_number, timeout=30,
#                 password=False, ommit_ping=False)
#         try:
#             if zk.connect():
#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'display_notification',
#                     'params': {
#                         'message': 'Successfully Connected',
#                         'type': 'success',
#                         'sticky': False
#                     }
#                 }
#         except Exception as error:
#             raise ValidationError(f'{error}')

#     def action_set_timezone(self):
#         """Function to set user's timezone to device"""
#         for info in self:
#             machine_ip = info.device_ip
#             zk_port = info.port_number
#             try:
#                 # Connecting with the device with the ip and port provided
#                 zk = ZK(machine_ip, port=zk_port, timeout=15,
#                         password=0,
#                         force_udp=False, ommit_ping=False)
#             except NameError:
#                 raise UserError(
#                     _("Pyzk module not Found. Please install it"
#                       "with 'pip3 install pyzk'."))
#             conn = self.device_connect(zk)
#             if conn:
#                 user_tz = self.env.context.get(
#                     'tz') or self.env.user.tz or 'UTC'
#                 user_timezone_time = pytz.utc.localize(fields.Datetime.now())
#                 user_timezone_time = user_timezone_time.astimezone(
#                     pytz.timezone(user_tz))
#                 conn.set_time(user_timezone_time)
#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'display_notification',
#                     'params': {
#                         'message': 'Successfully Set the Time',
#                         'type': 'success',
#                         'sticky': False
#                     }
#                 }
#             else:
#                 raise UserError(_(
#                     "Please Check the Connection"))

#     def action_clear_attendance(self):
#         """Methode to clear record from the zk.machine.attendance model and
#         from the device"""
#         for info in self:
#             try:
#                 machine_ip = info.device_ip
#                 zk_port = info.port_number
#                 try:
#                     # Connecting with the device
#                     zk = ZK(machine_ip, port=zk_port, timeout=30,
#                             password=0, force_udp=False, ommit_ping=False)
#                 except NameError:
#                     raise UserError(_(
#                         "Please install it with 'pip3 install pyzk'."))
#                 conn = self.device_connect(zk)
#                 if conn:
#                     conn.enable_device()
#                     clear_data = zk.get_attendance()
#                     if clear_data:
#                         # Clearing data in the device
#                         conn.clear_attendance()
#                         # Clearing data from attendance log
#                         self._cr.execute(
#                             """delete from zk_machine_attendance""")
#                         conn.disconnect()
#                     else:
#                         raise UserError(
#                             _('Unable to clear Attendance log.Are you sure '
#                               'attendance log is not empty.'))
#                 else:
#                     raise UserError(
#                         _('Unable to connect to Attendance Device. Please use '
#                           'Test Connection button to verify.'))
#             except Exception as error:
#                 raise ValidationError(f'{error}')

#     @api.model
#     def cron_download(self):
#         machines = self.env['biometric.device.details'].search([])
#         for machine in machines:
#             machine.action_download_attendance()

#     def action_download_attendance(self):
#         """Function to download attendance records from the device"""
#         _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
#         zk_attendance = self.env['zk.machine.attendance']
#         hr_attendance = self.env['hr.attendance']
#         for info in self:
#             machine_ip = info.device_ip
#             zk_port = info.port_number
#             try:
#                 # Connecting with the device with the ip and port provided
#                 zk = ZK(machine_ip, port=zk_port, timeout=15,
#                         password=0,
#                         force_udp=False, ommit_ping=False)
#             except NameError:
#                 raise UserError(
#                     _("Pyzk module not Found. Please install it"
#                       "with 'pip3 install pyzk'."))
#             conn = self.device_connect(zk)
#             self.action_set_timezone()
#             if conn:
#                 conn.disable_device()  # Device Cannot be used during this time.
#                 user = conn.get_users()
#                 attendance = conn.get_attendance()
#                 if attendance:
#                     for each in attendance:
#                         atten_time = each.timestamp
#                         local_tz = pytz.timezone(
#                             self.env.user.partner_id.tz or 'GMT')
#                         local_dt = local_tz.localize(atten_time, is_dst=None)
#                         utc_dt = local_dt.astimezone(pytz.utc)
#                         utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
#                         atten_time = datetime.datetime.strptime(
#                             utc_dt, "%Y-%m-%d %H:%M:%S")
#                         atten_time = fields.Datetime.to_string(atten_time)
#                         for uid in user:
#                             if uid.user_id == each.user_id:
#                                 get_user_id = self.env['hr.employee'].search(
#                                     [('device_id_num', '=', each.user_id)])
#                                 if get_user_id:
#                                     duplicate_atten_ids = zk_attendance.search(
#                                         [('device_id_num', '=', each.user_id),
#                                          ('punching_time', '=', atten_time)])
#                                     if not duplicate_atten_ids:
#                                         zk_attendance.create({
#                                             'employee_id': get_user_id.id,
#                                             'device_id_num': each.user_id,
#                                             'attendance_type': str(each.status),
#                                             'punch_type': str(each.punch),
#                                             'punching_time': atten_time,
#                                             'address_id': info.address_id.id
#                                         })
#                                         att_var = hr_attendance.search([(
#                                             'employee_id', '=', get_user_id.id),
#                                             ('check_out', '=', False)])
#                                         if each.punch == 0:  # check-in
#                                             if not att_var:
#                                                 hr_attendance.create({
#                                                     'employee_id':
#                                                         get_user_id.id,
#                                                     'check_in': atten_time
#                                                 })
#                                         if each.punch == 1:  # check-out
#                                             if len(att_var) == 1:
#                                                 att_var.write({
#                                                     'check_out': atten_time
#                                                 })
#                                             else:
#                                                 att_var1 = hr_attendance.search(
#                                                     [('employee_id', '=',
#                                                       get_user_id.id)])
#                                                 if att_var1:
#                                                     att_var1[-1].write({
#                                                         'check_out': atten_time
#                                                     })
#                                 else:
#                                     employee = self.env['hr.employee'].create({
#                                         'device_id_num': each.user_id,
#                                         'name': uid.name
#                                     })
#                                     zk_attendance.create({
#                                         'employee_id': employee.id,
#                                         'device_id_num': each.user_id,
#                                         'attendance_type': str(each.status),
#                                         'punch_type': str(each.punch),
#                                         'punching_time': atten_time,
#                                         'address_id': info.address_id.id
#                                     })
#                                     hr_attendance.create({
#                                         'employee_id': employee.id,
#                                         'check_in': atten_time
#                                     })
#                     conn.disconnect
#                     return True
#                 else:
#                     raise UserError(_('Unable to get the attendance log, please'
#                                       'try again later.'))
#             else:
#                 raise UserError(_('Unable to connect, please check the'
#                                   'parameters and network connections.'))














    # # ✅ Add the missing processed field
    # processed = fields.Boolean(string="Processed", default=False)

    # def action_process_attendance(self):
    #     """Move validated attendance records from `zk.machine.attendance` to `hr.attendance`."""
    #     zk_attendance_obj = self.env['zk.machine.attendance']
    #     hr_attendance_obj = self.env['hr.attendance']

    #     unprocessed_attendance = zk_attendance_obj.search([('processed', '=', False)])
    #     for record in unprocessed_attendance:
    #         employee = record.employee_id
    #         atten_time = record.punching_time

    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], limit=1)

    #         if record.attendance_type == '0':  # Check-In
    #             if open_attendance:
    #                 # If an attendance session is already open, close it before opening a new one
    #                 open_attendance.write({'check_out': atten_time})

    #             # Create new Check-In record
    #             # hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})

    #         elif record.attendance_type == '1':  # Check-Out
    #             if open_attendance:
    #                 open_attendance.write({'check_out': atten_time})
    #             else:
    #                 # If no Check-In exists, create a fallback record with both Check-In & Check-Out
    #                 # hr_attendance_obj.create({
    #                 #     'employee_id': employee.id,
    #                 #     'check_in': atten_time,
    #                 #     'check_out': atten_time
    #                 # })
    #                 x=0

    #         # Mark as processed
    #         record.write({'processed': True})

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }
    # def action_restart_device(self):
    #     """For restarting the device"""
    #     zk = ZK(self.device_ip, port=self.port_number, timeout=15,
    #             password=0,
    #             force_udp=False, ommit_ping=False)
    #     self.device_connect(zk).restart()
