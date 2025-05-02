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
from datetime import datetime, timedelta  # ✅ Ensure timedelta is imported
from pytz import timezone, utc  # ✅ Import timezone functions



_logger = logging.getLogger(__name__)

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



class MachineAttendance(models.Model):
    """Intermediate table to store biometric attendance before processing."""
    _name = 'zk.machine.attendance'
    _description = 'Biometric Attendance Log'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    device_id_num = fields.Char(string="Device ID", required=True)
    punching_time = fields.Datetime(string="Punching Time", required=True)
    address_id = fields.Many2one('res.partner', string="Location", default=lambda self: self._default_address_id)
    processed = fields.Boolean(string="Processed", default=False)
    attendance_type = fields.Selection([('0', 'Check In'), ('1', 'Check Out')], string="Attendance Type", required=True)
    punch_type = fields.Char(string="Punch Type")


    @api.model
    def _default_address_id(self):
        """Fetch the partner associated with the default company."""
        company = self.env.company
        return company.partner_id.id if company.partner_id else False



    def action_process_attendance_manual(self):
        """Manual button action to process attendance"""
        self.action_process_attendance()


    def action_process_attendance(self):
        """Process attendance based on employee shifts, prioritizing shift time constraints."""
        hr_attendance_obj = self.env['hr.attendance']
        now = fields.Datetime.now()

        # Fetch all attendance records sorted by time
        all_attendance_records = self.search([], order="punching_time asc")

        # Group attendance records by employee and shift time
        employee_attendance = {}
        for record in all_attendance_records:
            employee_id = record.device_id_num
            punch_date = record.punching_time.date()

            # 🔹 **Skip processing if the record is NOT in 2025**
            if punch_date.year != 2025:
                _logger.warning(f"⏳ Skipping attendance for {employee_id} on {punch_date} (Not in 2025)")
                continue

            if employee_id not in employee_attendance:
                employee_attendance[employee_id] = {}

            if punch_date not in employee_attendance[employee_id]:
                employee_attendance[employee_id][punch_date] = []

            employee_attendance[employee_id][punch_date].append(record.punching_time)

        ksa_tz = timezone('Asia/Riyadh')  # ✅ Define the KSA timezone
        for employee_id, dates in employee_attendance.items():
            employee = self.env['hr.employee'].search([('device_id_num', '=', employee_id)], limit=1)
            if not employee:
                _logger.warning(f"⚠️ No Employee Found for Device ID: {employee_id}")
                continue

            for punch_date, punch_times in dates.items():
                shift = employee.resource_calendar_id
                if not shift:
                    _logger.warning(f"⚠️ No Shift Found for Employee {employee.name} on {punch_date}")
                    continue

                shift_intervals = []
                for att in shift.attendance_ids:
                    if att.dayofweek == str(punch_date.weekday()):
                        # ✅ Convert Shift Time from KSA to UTC
                        shift_start_ksa = datetime.combine(punch_date, datetime.min.time()).replace(
                            hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0
                        )
                        shift_end_ksa = datetime.combine(punch_date, datetime.min.time()).replace(
                            hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0
                        )

                        shift_start_utc = ksa_tz.localize(shift_start_ksa).astimezone(utc)
                        shift_end_utc = ksa_tz.localize(shift_end_ksa).astimezone(utc)

                        shift_intervals.append((shift_start_utc, shift_end_utc))

                if not shift_intervals:
                    _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
                    continue

                punch_times.sort()  # Ensure punches are in chronological order

                for shift_start, shift_end in shift_intervals:
                    shift_punches = [p for p in punch_times if shift_start.replace(tzinfo=None) <= p.replace(tzinfo=None) <= shift_end.replace(tzinfo=None)]

                    if len(shift_punches) > 1:
                        check_in_time = shift_punches[0]
                        check_out_time = shift_punches[-1]
                        _logger.info(f"✅ Multiple punches for {employee.name} on {punch_date}: First IN {check_in_time}, Last OUT {check_out_time}")

                    elif len(shift_punches) == 1:
                        punch_time = shift_punches[0]
                        if abs((punch_time.replace(tzinfo=None) - shift_start.replace(tzinfo=None)).total_seconds()) <= \
                        abs((punch_time.replace(tzinfo=None) - shift_end.replace(tzinfo=None)).total_seconds()):
                            check_in_time = punch_time
                            check_out_time = shift_end - timedelta(hours=1)
                            _logger.info(f"⏳ Single Punch for {employee.name} on {punch_date}: Assigned IN {check_in_time}, OUT {check_out_time} (1 hour early)")
                        else:
                            check_in_time = shift_start + timedelta(hours=1)
                            check_out_time = punch_time
                            _logger.info(f"⏳ Single Punch for {employee.name} on {punch_date}: Assigned Late IN {check_in_time}, OUT {check_out_time}")

                    else:
                        _logger.warning(f"🚫 {employee.name} marked absent for shift {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')} on {punch_date}")
                        continue

                    if check_out_time.replace(tzinfo=None) < check_in_time.replace(tzinfo=None):
                        _logger.warning(f"❌ Error: Check-Out time {check_out_time} is before Check-In {check_in_time}, correcting...")
                        check_out_time = check_in_time + timedelta(minutes=1)

                    # 🔹 **Final Check: Ensure Attendance is Created ONLY in 2025**
                    if check_in_time.year != 2025 or check_out_time.year != 2025:
                        _logger.warning(f"⚠️ Skipping attendance for {employee.name} on {punch_date} (Check-In or Check-Out not in 2025)")
                        continue

                    # Check for existing attendance in the shift
                    existing_attendance = hr_attendance_obj.search([
                        ('employee_id', '=', employee.id),
                        ('check_in', '>=', shift_start),
                        ('check_in', '<=', shift_end)
                    ], limit=1)

                    if existing_attendance:
                        _logger.warning(f"⚠️ Skipping Duplicate Attendance for {employee.name} on {punch_date} in shift {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')}")
                        continue

                    # ✅ Create attendance record (Only if in 2025)
                    hr_attendance_obj.create({
                        'employee_id': employee.id,
                        'check_in': check_in_time.replace(tzinfo=None),
                        'check_out': check_out_time.replace(tzinfo=None)
                    })
                    _logger.info(f"✅ Attendance Recorded for {employee.name} on {punch_date}: IN {check_in_time}, OUT {check_out_time}")

# ########################8
#     def action_process_attendance(self):
#         """Process attendance based on employee shifts, prioritizing shift time constraints."""
#         hr_attendance_obj = self.env['hr.attendance']
#         now = fields.Datetime.now()

#         # Fetch all attendance records sorted by time
#         all_attendance_records = self.search([], order="punching_time asc")

#         # Group attendance records by employee and shift time
#         employee_attendance = {}
#         for record in all_attendance_records:
#             employee_id = record.device_id_num
#             punch_date = record.punching_time.date()

#             if employee_id not in employee_attendance:
#                 employee_attendance[employee_id] = {}

#             if punch_date not in employee_attendance[employee_id]:
#                 employee_attendance[employee_id][punch_date] = []

#             employee_attendance[employee_id][punch_date].append(record.punching_time)

#         ksa_tz = timezone('Asia/Riyadh')  # ✅ Define the KSA timezone
#         for employee_id, dates in employee_attendance.items():
#             employee = self.env['hr.employee'].search([('device_id_num', '=', employee_id)], limit=1)
#             if not employee:
#                 _logger.warning(f"⚠️ No Employee Found for Device ID: {employee_id}")
#                 continue

#             for punch_date, punch_times in dates.items():
#                 shift = employee.resource_calendar_id
#                 if not shift:
#                     _logger.warning(f"⚠️ No Shift Found for Employee {employee.name} on {punch_date}")
#                     continue

#                 shift_intervals = []
#                 for att in shift.attendance_ids:
#                     if att.dayofweek == str(punch_date.weekday()):


#                         # ✅ Convert Shift Time from KSA to UTC
#                         shift_start_ksa = datetime.combine(punch_date, datetime.min.time()).replace(
#                             hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0
#                         )
#                         shift_end_ksa = datetime.combine(punch_date, datetime.min.time()).replace(
#                             hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0
#                         )

#                         shift_start_utc = ksa_tz.localize(shift_start_ksa).astimezone(utc)
#                         shift_end_utc = ksa_tz.localize(shift_end_ksa).astimezone(utc)

#                         shift_intervals.append((shift_start_utc, shift_end_utc))



#                         # shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
#                         #     hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0
#                         # )
#                         # shift_end = datetime.combine(punch_date, datetime.min.time()).replace(
#                         #     hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0
#                         # )
#                         # shift_intervals.append((shift_start, shift_end))

#                 if not shift_intervals:
#                     _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
#                     continue

#                 punch_times.sort()  # Ensure punches are in chronological order

#                 for shift_start, shift_end in shift_intervals:
#                     # shift_punches = [p for p in punch_times if shift_start <= p <= shift_end]
#                     shift_punches = [  p for p in punch_times   if shift_start.replace(tzinfo=None) <= p.replace(tzinfo=None) <= shift_end.replace(tzinfo=None)]

#                     if len(shift_punches) > 1:
#                         # 🔹 Multiple Check-Ins and Check-Outs in a Shift: Use first check-in and last check-out
#                         check_in_time = shift_punches[0]
#                         check_out_time = shift_punches[-1]
#                         _logger.info(f"✅ Multiple punches for {employee.name} on {punch_date}: First IN {check_in_time}, Last OUT {check_out_time}")

#                     elif len(shift_punches) == 1:
#                         # 🔹 Single Punch: Determine check-in or check-out based on proximity
#                         punch_time = shift_punches[0]
#                         # if abs((punch_time - shift_start).total_seconds()) <= abs((punch_time - shift_end).total_seconds()):
#                         if abs((punch_time.replace(tzinfo=None) - shift_start.replace(tzinfo=None)).total_seconds()) <= \
#                            abs((punch_time.replace(tzinfo=None) - shift_end.replace(tzinfo=None)).total_seconds()):


#                             # Punch is closer to shift start, consider it a check-in
#                             check_in_time = punch_time
#                             check_out_time = shift_end - timedelta(hours=1)  # Early check-out
#                             _logger.info(f"⏳ Single Punch for {employee.name} on {punch_date}: Assigned IN {check_in_time}, OUT {check_out_time} (1 hour early)")
#                         else:
#                             # Punch is closer to shift end, consider it a check-out
#                             check_in_time = shift_start + timedelta(hours=1)  # Late check-in
#                             check_out_time = punch_time
#                             _logger.info(f"⏳ Single Punch for {employee.name} on {punch_date}: Assigned Late IN {check_in_time}, OUT {check_out_time}")

#                     else:
#                         # 🔹 No Punches for this Shift: Mark as absent (No attendance record created)
#                         _logger.warning(f"🚫 {employee.name} marked absent for shift {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')} on {punch_date}")
#                         continue

#                     # Ensure check-out is after check-in
#                     # if check_out_time < check_in_time:
#                     if check_out_time.replace(tzinfo=None) < check_in_time.replace(tzinfo=None):

#                         _logger.warning(f"❌ Error: Check-Out time {check_out_time} is before Check-In {check_in_time}, correcting...")
#                         check_out_time = check_in_time + timedelta(minutes=1)  # Force valid checkout

#                     # Check for existing attendance for this shift
#                     existing_attendance = hr_attendance_obj.search([
#                         ('employee_id', '=', employee.id),
#                         ('check_in', '>=', shift_start),
#                         ('check_in', '<=', shift_end)
#                     ], limit=1)

#                     if existing_attendance:
#                         _logger.warning(f"⚠️ Skipping Duplicate Attendance for {employee.name} on {punch_date} in shift {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')}")
#                         continue  # Skip duplicate attendance

#                     # ✅ Create attendance record
#                     hr_attendance_obj.create({
#                         'employee_id': employee.id,
#                         'check_in': check_in_time.replace(tzinfo=None),
#                         'check_out': check_out_time.replace(tzinfo=None)
#                     })
#                     _logger.info(f"✅ Attendance Recorded for {employee.name} on {punch_date}: IN {check_in_time}, OUT {check_out_time}")

        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'message': 'Attendance processed successfully with shift-based calculations!',
        #         'type': 'success',
        #         'sticky': False
        #     }
        # }
