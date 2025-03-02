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

########################8
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



                        # shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
                        #     hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0
                        # )
                        # shift_end = datetime.combine(punch_date, datetime.min.time()).replace(
                        #     hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0
                        # )
                        # shift_intervals.append((shift_start, shift_end))

                if not shift_intervals:
                    _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
                    continue

                punch_times.sort()  # Ensure punches are in chronological order

                for shift_start, shift_end in shift_intervals:
                    # shift_punches = [p for p in punch_times if shift_start <= p <= shift_end]
                    shift_punches = [  p for p in punch_times   if shift_start.replace(tzinfo=None) <= p.replace(tzinfo=None) <= shift_end.replace(tzinfo=None)]

                    if len(shift_punches) > 1:
                        # 🔹 Multiple Check-Ins and Check-Outs in a Shift: Use first check-in and last check-out
                        check_in_time = shift_punches[0]
                        check_out_time = shift_punches[-1]
                        _logger.info(f"✅ Multiple punches for {employee.name} on {punch_date}: First IN {check_in_time}, Last OUT {check_out_time}")

                    elif len(shift_punches) == 1:
                        # 🔹 Single Punch: Determine check-in or check-out based on proximity
                        punch_time = shift_punches[0]
                        # if abs((punch_time - shift_start).total_seconds()) <= abs((punch_time - shift_end).total_seconds()):
                        if abs((punch_time.replace(tzinfo=None) - shift_start.replace(tzinfo=None)).total_seconds()) <= \
                           abs((punch_time.replace(tzinfo=None) - shift_end.replace(tzinfo=None)).total_seconds()):


                            # Punch is closer to shift start, consider it a check-in
                            check_in_time = punch_time
                            check_out_time = shift_end - timedelta(hours=1)  # Early check-out
                            _logger.info(f"⏳ Single Punch for {employee.name} on {punch_date}: Assigned IN {check_in_time}, OUT {check_out_time} (1 hour early)")
                        else:
                            # Punch is closer to shift end, consider it a check-out
                            check_in_time = shift_start + timedelta(hours=1)  # Late check-in
                            check_out_time = punch_time
                            _logger.info(f"⏳ Single Punch for {employee.name} on {punch_date}: Assigned Late IN {check_in_time}, OUT {check_out_time}")

                    else:
                        # 🔹 No Punches for this Shift: Mark as absent (No attendance record created)
                        _logger.warning(f"🚫 {employee.name} marked absent for shift {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')} on {punch_date}")
                        continue

                    # Ensure check-out is after check-in
                    # if check_out_time < check_in_time:
                    if check_out_time.replace(tzinfo=None) < check_in_time.replace(tzinfo=None):

                        _logger.warning(f"❌ Error: Check-Out time {check_out_time} is before Check-In {check_in_time}, correcting...")
                        check_out_time = check_in_time + timedelta(minutes=1)  # Force valid checkout

                    # Check for existing attendance for this shift
                    existing_attendance = hr_attendance_obj.search([
                        ('employee_id', '=', employee.id),
                        ('check_in', '>=', shift_start),
                        ('check_in', '<=', shift_end)
                    ], limit=1)

                    if existing_attendance:
                        _logger.warning(f"⚠️ Skipping Duplicate Attendance for {employee.name} on {punch_date} in shift {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')}")
                        continue  # Skip duplicate attendance

                    # ✅ Create attendance record
                    hr_attendance_obj.create({
                        'employee_id': employee.id,
                        'check_in': check_in_time.replace(tzinfo=None),
                        'check_out': check_out_time.replace(tzinfo=None)
                    })
                    _logger.info(f"✅ Attendance Recorded for {employee.name} on {punch_date}: IN {check_in_time}, OUT {check_out_time}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Attendance processed successfully with shift-based calculations!',
                'type': 'success',
                'sticky': False
            }
        }


########################7



    # def action_process_attendance(self):
    #     """Process attendance based on shift times with auto check-in, check-out, and absence marking."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     # Fetch all attendance records sorted by time
    #     all_attendance_records = self.search([], order="punching_time asc")

    #     # Group attendance records by employee and date
    #     employee_attendance = {}
    #     for record in all_attendance_records:
    #         employee_id = record.device_id_num
    #         punch_date = record.punching_time.date()

    #         if employee_id not in employee_attendance:
    #             employee_attendance[employee_id] = {}

    #         if punch_date not in employee_attendance[employee_id]:
    #             employee_attendance[employee_id][punch_date] = []

    #         employee_attendance[employee_id][punch_date].append(record.punching_time)

    #     for employee_id, dates in employee_attendance.items():
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', employee_id)], limit=1)
    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {employee_id}")
    #             continue

    #         for punch_date, punch_times in dates.items():
    #             shift = employee.resource_calendar_id
    #             if not shift:
    #                 _logger.warning(f"⚠️ No Shift Found for Employee {employee.name} on {punch_date}")
    #                 continue

    #             shift_times = shift.attendance_ids  # Get shift rules
    #             shift_start, shift_end = None, None

    #             for att in shift_times:
    #                 if att.dayofweek == str(punch_date.weekday()):
    #                     shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
    #                         hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0
    #                     )
    #                     shift_end = datetime.combine(punch_date, datetime.min.time()).replace(
    #                         hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0
    #                     )

    #             if not shift_start or not shift_end:
    #                 _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
    #                 continue

    #             punch_times.sort()  # Ensure punches are in chronological order

    #             if len(punch_times) > 1:
    #                 # 🔹 Multiple Check-Ins and Check-Outs: Use first check-in and last check-out
    #                 check_in_time = punch_times[0]
    #                 check_out_time = punch_times[-1]

    #                 _logger.info(f"✅ Multiple punches for {employee.name} on {punch_date}: First IN {check_in_time}, Last OUT {check_out_time}")

    #             elif len(punch_times) == 1:
    #                 # 🔹 Only One Punch: Determine if it's closer to check-in or check-out
    #                 punch_time = punch_times[0]
    #                 if abs((punch_time - shift_start).total_seconds()) <= abs((punch_time - shift_end).total_seconds()):
    #                     # Punch is closer to shift start, consider it a check-in
    #                     check_in_time = punch_time
    #                     check_out_time = shift_end - timedelta(hours=1)  # Early check-out
    #                     _logger.info(f"⏳ Only One Punch for {employee.name} on {punch_date}: Assigned IN {check_in_time}, OUT {check_out_time} (1 hour early)")
    #                 else:
    #                     # Punch is closer to shift end, consider it a check-out
    #                     check_in_time = shift_start + timedelta(hours=1)  # Late check-in
    #                     check_out_time = punch_time
    #                     _logger.info(f"⏳ Only One Punch for {employee.name} on {punch_date}: Assigned Late IN {check_in_time}, OUT {check_out_time}")

    #             else:
    #                 # 🔹 No Punches Recorded: Mark as absent (No attendance record created)
    #                 _logger.warning(f"🚫 {employee.name} marked absent on {punch_date} (No punches)")
    #                 continue

    #             # Ensure check-out is after check-in
    #             if check_out_time < check_in_time:
    #                 _logger.warning(f"❌ Error: Check-Out time {check_out_time} is before Check-In {check_in_time}, correcting...")
    #                 check_out_time = check_in_time + timedelta(minutes=1)  # Force valid checkout

    #             # Check for existing attendance for this date
    #             existing_attendance = hr_attendance_obj.search([
    #                 ('employee_id', '=', employee.id),
    #                 ('check_in', '>=', shift_start),
    #                 ('check_in', '<=', shift_end)
    #             ], limit=1)

    #             if existing_attendance:
    #                 _logger.warning(f"⚠️ Skipping Duplicate Attendance for {employee.name} on {punch_date}")
    #                 continue  # Skip duplicate attendance

    #             # ✅ Create attendance record
    #             hr_attendance_obj.create({
    #                 'employee_id': employee.id,
    #                 'check_in': check_in_time,
    #                 'check_out': check_out_time
    #             })
    #             _logger.info(f"✅ Attendance Recorded for {employee.name}: IN {check_in_time}, OUT {check_out_time}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with automatic check-in/out assignments!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }



########################6

    # def action_process_attendance(self):
    #     """Process attendance, ensuring no duplicate check-ins and proper check-out handling."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     all_attendance_records = self.search([], order="punching_time asc")

    #     for record in all_attendance_records:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         punch_time = record.punching_time
    #         punch_date = punch_time.date()

    #         # Retrieve shift details
    #         shift = employee.resource_calendar_id
    #         if not shift:
    #             _logger.warning(f"⚠️ No Shift Found for Employee {employee.name}, skipping attendance.")
    #             continue

    #         shift_times = shift.attendance_ids  # Get shift rules
    #         if not shift_times:
    #             _logger.warning(f"⚠️ No Shift Timings Defined for {employee.name}, skipping attendance.")
    #             continue

    #         shift_start, shift_end = None, None
    #         for att in shift_times:
    #             if att.dayofweek == str(punch_date.weekday()):
    #                 shift_start = punch_time.replace(hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0)
    #                 shift_end = punch_time.replace(hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0)

    #         if not shift_start or not shift_end:
    #             _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}, skipping attendance.")
    #             continue

    #         # 🔹 Check for open check-ins without check-out
    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], order="check_in asc", limit=1)

    #         if open_attendance:
    #             # Apply early check-out (1 hour before shift end) if check-out is missing
    #             early_checkout_time = max(open_attendance.check_in + timedelta(minutes=1), shift_end - timedelta(hours=1))

    #             # Ensure check-out is never before check-in
    #             if early_checkout_time < open_attendance.check_in:
    #                 early_checkout_time = open_attendance.check_in + timedelta(minutes=1)

    #             open_attendance.write({'check_out': early_checkout_time})
    #             _logger.info(f"✅ Auto Early Check-Out for {employee.name} at {early_checkout_time} (1 hour before shift end)")

    #         # 🔹 Prevent duplicate check-in on the same day
    #         existing_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_in', '>=', punch_time.replace(hour=0, minute=0, second=0)),  # Check for same-day records
    #         ], limit=1)

    #         if existing_attendance:
    #             _logger.warning(f"⚠️ Duplicate Check-In Skipped for {employee.name} at {punch_time}")
    #             continue  # Skip duplicate check-ins

    #         hr_attendance_obj.create({
    #             'employee_id': employee.id,
    #             'check_in': punch_time
    #         })
    #         _logger.info(f"✅ New Check-In Recorded: {employee.name} at {punch_time}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with early check-outs for missing check-outs!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }


#######################5
    # def action_process_attendance(self):
    #     """Process attendance, ensuring all check-ins are checked out before creating new ones."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     all_attendance_records = self.search([], order="punching_time asc")

    #     for record in all_attendance_records:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         punch_time = record.punching_time
    #         punch_date = punch_time.date()

    #         # Retrieve shift details
    #         shift = employee.resource_calendar_id
    #         if not shift:
    #             _logger.warning(f"⚠️ No Shift Found for Employee {employee.name}")
    #             continue

    #         shift_times = shift.attendance_ids  # Get shift rules
    #         if not shift_times:
    #             _logger.warning(f"⚠️ No Shift Timings Defined for {employee.name}")
    #             continue

    #         shift_start, shift_end = None, None
    #         for att in shift_times:
    #             if att.dayofweek == str(punch_date.weekday()):
    #                 shift_start = punch_time.replace(hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0)
    #                 shift_end = punch_time.replace(hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0)

    #         if not shift_start or not shift_end:
    #             _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
    #             continue

    #         # 🔹 Check for open check-ins without check-out
    #         open_attendances = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], order="check_in asc")

    #         for open_att in open_attendances:
    #             # Apply early check-out (1 hour before shift end) if check-out is missing
    #             early_checkout_time = max(open_att.check_in + timedelta(minutes=1), shift_end - timedelta(hours=1))

    #             # Ensure check-out is never before check-in
    #             if early_checkout_time < open_att.check_in:
    #                 early_checkout_time = open_att.check_in + timedelta(minutes=1)

    #             open_att.write({'check_out': early_checkout_time})
    #             _logger.info(f"✅ Auto Early Check-Out for {employee.name} at {early_checkout_time} (1 hour before shift end)")

    #         # 🔹 Now, create a new check-in for the current shift
    #         check_in_time = max(shift_start, punch_time)  # Ensure it aligns with shift start
    #         existing_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_in', '>=', punch_time.replace(hour=0, minute=0, second=0)),  # Check for same-day records
    #         ], limit=1)

    #         if existing_attendance:
    #             _logger.warning(f"⚠️ Duplicate Check-In Skipped for {employee.name} at {punch_time}")
    #             continue  # Skip duplicate check-ins

    #         hr_attendance_obj.create({
    #             'employee_id': employee.id,
    #             'check_in': check_in_time
    #         })
    #         _logger.info(f"✅ New Check-In Recorded: {employee.name} at {check_in_time}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with early check-outs for missing check-outs!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }



################4
    # def action_process_attendance(self):
    #     """Process attendance by ensuring check-in and check-out are correctly assigned."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     all_attendance_records = self.search([], order="punching_time asc")

    #     for record in all_attendance_records:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         punch_time = record.punching_time
    #         punch_date = punch_time.date()

    #         # Retrieve shift details
    #         shift = employee.resource_calendar_id
    #         if not shift:
    #             _logger.warning(f"⚠️ No Shift Found for Employee {employee.name}")
    #             continue

    #         shift_times = shift.attendance_ids  # Get the shift rules
    #         if not shift_times:
    #             _logger.warning(f"⚠️ No Shift Timings Defined for {employee.name}")
    #             continue

    #         shift_start, shift_end = None, None
    #         for att in shift_times:
    #             if att.dayofweek == str(punch_date.weekday()):
    #                 shift_start = punch_time.replace(hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0)
    #                 shift_end = punch_time.replace(hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0)

    #         if not shift_start or not shift_end:
    #             _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
    #             continue

    #         # 🔹 Check if an open check-in exists
    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], order="check_in asc", limit=1)

    #         if open_attendance:
    #             # **FIX: Ensure check-out is after check-in**
    #             check_out_time = max(open_attendance.check_in + timedelta(minutes=1), punch_time)  # Ensure it's later
    #             if check_out_time < open_attendance.check_in:
    #                 check_out_time = open_attendance.check_in + timedelta(minutes=1)  # Force a valid time

    #             open_attendance.write({'check_out': check_out_time})
    #             _logger.info(f"✅ Auto Check-Out for {employee.name} at {check_out_time}")

    #         else:
    #             # 🔹 Now, create a new check-in for the current shift
    #             check_in_time = max(shift_start, punch_time)  # Ensure it aligns with shift start
    #             hr_attendance_obj.create({
    #                 'employee_id': employee.id,
    #                 'check_in': check_in_time
    #             })
    #             _logger.info(f"✅ New Check-In Recorded: {employee.name} at {check_in_time}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with corrected check-in/out times!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }

############3 BEST one

    # def action_process_attendance(self):
    #     """Process attendance by correctly handling check-in and check-out based on shift timings."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     all_attendance_records = self.search([], order="punching_time asc")

    #     for record in all_attendance_records:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         punch_time = record.punching_time
    #         punch_date = punch_time.date()

    #         # Retrieve employee shift timings
    #         shift = employee.resource_calendar_id
    #         if not shift:
    #             _logger.warning(f"⚠️ No Shift Found for Employee {employee.name}")
    #             continue

    #         shift_times = shift.attendance_ids  # Get the shift rules
    #         if not shift_times:
    #             _logger.warning(f"⚠️ No Shift Timings Defined for {employee.name}")
    #             continue

    #         shift_start, shift_end = None, None
    #         for att in shift_times:
    #             if att.dayofweek == str(punch_date.weekday()):
    #                 shift_start = punch_time.replace(hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0)
    #                 shift_end = punch_time.replace(hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0)

    #         if not shift_start or not shift_end:
    #             _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
    #             continue

    #         # 🔹 Check if an open check-in exists for this employee
    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], order="check_in asc", limit=1)

    #         if open_attendance:
    #             # ✅ Close the existing check-in before recording a new one
    #             check_out_time = max(shift_start, punch_time)  # Ensure check-out aligns with shift start
    #             open_attendance.write({'check_out': check_out_time})
    #             _logger.info(f"✅ Auto Check-Out for {employee.name} at {check_out_time}")

    #         # 🔹 Now, create a new check-in for the current shift
    #         check_in_time = max(shift_start, punch_time)  # Ensure check-in aligns with shift start
    #         existing_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_in', '>=', punch_time.replace(hour=0, minute=0, second=0)),  # Check for same-day records
    #         ], limit=1)

    #         if not existing_attendance:
    #             hr_attendance_obj.create({
    #                 'employee_id': employee.id,
    #                 'check_in': check_in_time
    #             })
    #             _logger.info(f"✅ New Check-In Recorded: {employee.name} at {check_in_time}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with corrected check-in/out times!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }

##############2
    # def action_process_attendance(self):
    #     """Process attendance based on employee shift times, handling missing check-ins/check-outs."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     all_attendance_records = self.search([], order="punching_time asc")

    #     for record in all_attendance_records:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         punch_time = record.punching_time
    #         punch_date = punch_time.date()

    #         # Retrieve the employee's assigned shift times (morning/evening)
    #         shift = employee.resource_calendar_id  # Employee's assigned shift
    #         if not shift:
    #             _logger.warning(f"⚠️ No Shift Found for Employee {employee.name}")
    #             continue

    #         shift_times = shift.attendance_ids  # Get the shift rules
    #         if not shift_times:
    #             _logger.warning(f"⚠️ No Shift Timings Defined for {employee.name}")
    #             continue

    #         # Determine the shift start & end time for the current day
    #         shift_start, shift_end = None, None
    #         for att in shift_times:
    #             if att.dayofweek == str(punch_date.weekday()):  # Match the shift with the weekday
    #                 shift_start = punch_time.replace(hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60), second=0)
    #                 shift_end = punch_time.replace(hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60), second=0)

    #         if not shift_start or not shift_end:
    #             _logger.warning(f"⚠️ No Shift Timings for Employee {employee.name} on {punch_date}")
    #             continue

    #         # 🔹 Handle missed check-in (Late by 1 hour)
    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], order="check_in asc", limit=1)

    #         if not open_attendance:  # No open check-in found, means this is a check-in attempt
    #             check_in_time = punch_time

    #             # If the employee forgot to check-in, mark as late
    #             if check_in_time > shift_start + timedelta(hours=1):
    #                 check_in_time = shift_start + timedelta(hours=1)
    #                 note = f"Late check-in recorded (Missed actual shift start at {shift_start.strftime('%H:%M')})"
    #                 _logger.info(f"⏳ Late Check-in for {employee.name} at {check_in_time}. Note: {note}")

    #             # Create the check-in entry
    #             hr_attendance_obj.create({
    #                 'employee_id': employee.id,
    #                 'check_in': check_in_time,
    #                 'notes': note if 'note' in locals() else ''
    #             })
    #             _logger.info(f"✅ New Check-In Recorded: {employee.name} at {check_in_time}")

    #         else:
    #             # 🔹 Handle missed check-out (Early check-out by 1 hour)
    #             check_out_time = punch_time

    #             # If the employee forgot to check-out, mark as early check-out
    #             if check_out_time > shift_end:
    #                 check_out_time = shift_end - timedelta(hours=1)
    #                 note = f"Early check-out recorded (Missed actual shift end at {shift_end.strftime('%H:%M')})"
    #                 _logger.info(f"⏳ Early Check-out for {employee.name} at {check_out_time}. Note: {note}")

    #             # Update the existing check-in record with the check-out time
    #             open_attendance.write({
    #                 'check_out': check_out_time,
    #                 'notes': note if 'note' in locals() else ''
    #             })
    #             _logger.info(f"✅ Check-Out Recorded: {employee.name} at {check_out_time}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with automatic adjustments for late/early check-outs!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }

############1
    # def action_process_attendance(self):
    #     """Automatically process attendance based on time ranges without using punch type."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     all_attendance_records = self.search([], order="punching_time asc")

    #     for record in all_attendance_records:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         punch_time = record.punching_time
    #         punch_hour = punch_time.hour + punch_time.minute / 60  # Convert to decimal hours

    #         # Define shift timings
    #         morning_start = 8.0   # 8:00 AM
    #         morning_end = 12.75   # 12:45 PM
    #         evening_start = 16.0  # 4:00 PM
    #         evening_end = 20.5    # 8:30 PM

    #         # Determine if the punch belongs to Morning or Evening shift
    #         if morning_start <= punch_hour <= morning_end:
    #             shift_type = 'morning'
    #         elif evening_start <= punch_hour <= evening_end:
    #             shift_type = 'evening'
    #         else:
    #             _logger.warning(f"⚠️ Ignored Punch: {punch_time} (Out of Defined Shift Times)")
    #             continue  # Ignore punches outside defined shifts

    #         # Search for an existing open attendance for the employee
    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], order="check_in asc", limit=1)

    #         if open_attendance:
    #             # Close previous attendance before creating a new one
    #             _logger.info(f"⏳ Closing previous open attendance for {employee.name} at {open_attendance.check_in}")
    #             open_attendance.write({'check_out': punch_time})

    #         # Create a new check-in record
    #         hr_attendance_obj.create({
    #             'employee_id': employee.id,
    #             'check_in': punch_time
    #         })
    #         _logger.info(f"✅ New Check-In Recorded: {employee.name} at {punch_time}")

    #     # ✅ Auto-close remaining check-ins after shift ends
    #     open_attendances = hr_attendance_obj.search([
    #         ('check_out', '=', False),
    #         ('check_in', '<=', now - timedelta(hours=4))  # Auto close check-ins older than 4 hours
    #     ])
    #     for open_att in open_attendances:
    #         shift_cutoff = open_att.check_in.replace(hour=12, minute=45) if open_att.check_in.hour < 16 else open_att.check_in.replace(hour=20, minute=30)
    #         auto_checkout = min(shift_cutoff, now)  # Use shift end or current time (whichever is earlier)
    #         open_att.write({'check_out': auto_checkout})
    #         _logger.info(f"⏳ Auto Check-Out Applied for {open_att.employee_id.name} at {auto_checkout}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with automatic check-out fixes!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }

# ########################################################################################################################################################
#     def action_process_attendance(self):
#         """Automatically process attendance and avoid duplicate check-ins."""
#         hr_attendance_obj = self.env['hr.attendance']
#         now = fields.Datetime.now()

#         all_attendance_records = self.search([], order="punching_time asc")

#         for record in all_attendance_records:
#             employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

#             if not employee:
#                 _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
#                 continue

#             punch_time = record.punching_time
#             punch_hour = punch_time.hour + punch_time.minute / 60  # Convert to decimal hours

#             # Define shift timings
#             morning_start = 8.0   # 8:00 AM
#             morning_end = 12.75   # 12:45 PM
#             evening_start = 16.0  # 4:00 PM
#             evening_end = 20.5    # 8:30 PM

#             # Determine if the punch belongs to Morning or Evening shift
#             if morning_start <= punch_hour <= morning_end:
#                 shift_type = 'morning'
#             elif evening_start <= punch_hour <= evening_end:
#                 shift_type = 'evening'
#             else:
#                 _logger.warning(f"⚠️ Ignored Punch: {punch_time} (Out of Defined Shift Times)")
#                 continue  # Ignore punches outside defined shifts

#             # 🔹 Check if the employee already has an open check-in
#             open_attendance = hr_attendance_obj.search([
#                 ('employee_id', '=', employee.id),
#                 ('check_out', '=', False)
#             ], order="check_in asc", limit=1)

#             if open_attendance:
#                 # ✅ Auto-check-out before adding a new check-in
#                 _logger.info(f"⏳ Closing previous open attendance for {employee.name} at {open_attendance.check_in}")
#                 open_attendance.write({'check_out': punch_time})

#             # 🔹 Prevent multiple check-ins in the same shift
#             existing_attendance = hr_attendance_obj.search([
#                 ('employee_id', '=', employee.id),
#                 ('check_in', '>=', punch_time.replace(hour=0, minute=0, second=0))  # Same-day check-in
#             ], limit=1)

#             if existing_attendance:
#                 _logger.warning(f"⚠️ Duplicate Check-In Skipped for {employee.name} at {punch_time}")
#                 continue  # Skip duplicate check-ins

#             # ✅ Create a new check-in record
#             hr_attendance_obj.create({
#                 'employee_id': employee.id,
#                 'check_in': punch_time
#             })
#             _logger.info(f"✅ New Check-In Recorded: {employee.name} at {punch_time}")

#         # ✅ Auto-close remaining check-ins after shift ends
#         open_attendances = hr_attendance_obj.search([
#             ('check_out', '=', False),
#             ('check_in', '<=', now - timedelta(hours=4))  # Auto close check-ins older than 4 hours
#         ])
#         for open_att in open_attendances:
#             shift_cutoff = open_att.check_in.replace(hour=12, minute=45) if open_att.check_in.hour < 16 else open_att.check_in.replace(hour=20, minute=30)
#             auto_checkout = min(shift_cutoff, now)  # Use shift end or current time (whichever is earlier)
#             open_att.write({'check_out': auto_checkout})
#             _logger.info(f"⏳ Auto Check-Out Applied for {open_att.employee_id.name} at {auto_checkout}")

#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'message': 'Attendance processed successfully with automatic check-out fixes!',
#                 'type': 'success',
#                 'sticky': False
#             }
#         }

##################################################################################################################








# class MachineAttendance(models.Model):
#     """Intermediate table to store biometric attendance before processing."""
#     _name = 'zk.machine.attendance'
#     _description = 'Biometric Attendance Log'

#     employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
#     device_id_num = fields.Char(string="Device ID", required=True)
#     attendance_type = fields.Selection([('0', 'Check In'), ('1', 'Check Out')], string="Attendance Type", required=True)
#     punch_type = fields.Char(string="Punch Type")
#     punching_time = fields.Datetime(string="Punching Time", required=True)
#     address_id = fields.Many2one('res.partner', string="Location", default=lambda self: self._default_address_id)
#     processed = fields.Boolean(string="Processed", default=False)



#     @api.model
#     def _default_address_id(self):
#         """Fetch the partner associated with the default company."""
#         company = self.env.company  # Get the current user's default company
#         return company.partner_id.id if company.partner_id else False

#     def action_process_attendance(self):
#         """Automatically process attendance based on time ranges without using punch type."""
#         hr_attendance_obj = self.env['hr.attendance']
#         now = fields.Datetime.now()

#         # unprocessed_attendance = self.search([('processed', '=', False)], order="punching_time asc")
#         unprocessed_attendance = self.search([], order="punching_time asc")

#         for record in unprocessed_attendance:
#             employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

#             if not employee:
#                 _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
#                 continue

#             punch_time = record.punching_time
#             punch_hour = punch_time.hour + punch_time.minute / 60  # Convert to decimal hours

#             # Define shift timings
#             morning_start = 8.0   # 8:00 AM
#             morning_end = 12.75   # 12:45 PM
#             evening_start = 16.0  # 4:00 PM
#             evening_end = 20.5    # 8:30 PM

#             # Determine if the punch belongs to Morning or Evening shift
#             if morning_start <= punch_hour <= morning_end:
#                 shift_type = 'morning'
#             elif evening_start <= punch_hour <= evening_end:
#                 shift_type = 'evening'
#             else:
#                 _logger.warning(f"⚠️ Ignored Punch: {punch_time} (Out of Defined Shift Times)")
#                 continue  # Ignore punches outside defined shifts

#             # Search for an existing open attendance for the shift
#             open_attendance = hr_attendance_obj.search([
#                 ('employee_id', '=', employee.id),
#                 ('check_out', '=', False),
#                 ('check_in', '>=', punch_time.replace(hour=0, minute=0, second=0)),  # Same day check-in
#             ], limit=1)

#             if open_attendance:
#                 # If the punch is later than check-in, mark it as check-out
#                 if punch_time > open_attendance.check_in:
#                     open_attendance.write({'check_out': punch_time})
#                     _logger.info(f"✅ Check-Out Recorded: {employee.name} at {punch_time}")
#             else:
#                 # Create a new check-in for this shift
#                 hr_attendance_obj.create({
#                     'employee_id': employee.id,
#                     'check_in': punch_time
#                 })
#                 _logger.info(f"✅ Check-In Recorded: {employee.name} at {punch_time}")

#             # ✅ Mark record as processed
#             record.write({'processed': True})

#         # ✅ Auto-close remaining check-ins after shift ends
#         open_attendances = hr_attendance_obj.search([
#             ('check_out', '=', False),
#             ('check_in', '<=', now - timedelta(hours=4))  # Auto close check-ins older than 4 hours
#         ])
#         for open_att in open_attendances:
#             shift_cutoff = open_att.check_in.replace(hour=12, minute=45) if open_att.check_in.hour < 16 else open_att.check_in.replace(hour=20, minute=30)
#             auto_checkout = min(shift_cutoff, now)  # Use shift end or current time (whichever is earlier)
#             open_att.write({'check_out': auto_checkout})
#             _logger.info(f"⏳ Auto Check-Out Applied for {open_att.employee_id.name} at {auto_checkout}")

#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'message': 'Attendance processed successfully with automatic check-in and check-out!',
#                 'type': 'success',
#                 'sticky': False
#             }
#         }







    # def action_process_attendance(self):
    #     """Automatically process attendance based on time ranges without using punch type."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     unprocessed_attendance = self.search([('processed', '=', False)], order="punching_time asc")

    #     for record in unprocessed_attendance:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         punch_time = record.punching_time
    #         punch_hour = punch_time.hour + punch_time.minute / 60  # Convert to decimal hours

    #         # Define shift timings
    #         morning_start = 8.0   # 8:00 AM
    #         morning_end = 12.75   # 12:45 PM
    #         evening_start = 16.0  # 4:00 PM
    #         evening_end = 20.5    # 8:30 PM

    #         # Determine if the punch belongs to Morning or Evening shift
    #         if morning_start <= punch_hour <= morning_end:
    #             shift_type = 'morning'
    #         elif evening_start <= punch_hour <= evening_end:
    #             shift_type = 'evening'
    #         else:
    #             _logger.warning(f"⚠️ Ignored Punch: {punch_time} (Out of Defined Shift Times)")
    #             continue  # Ignore punches outside defined shifts

    #         # Search for an existing open attendance for the shift
    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False),
    #             ('check_in', '>=', punch_time.replace(hour=0, minute=0, second=0)),  # Same day check-in
    #         ], limit=1)

    #         if open_attendance:
    #             # If the punch is later than check-in, mark it as check-out
    #             if punch_time > open_attendance.check_in:
    #                 open_attendance.write({'check_out': punch_time})
    #                 _logger.info(f"✅ Check-Out Recorded: {employee.name} at {punch_time}")
    #         else:
    #             # Create a new check-in for this shift
    #             hr_attendance_obj.create({
    #                 'employee_id': employee.id,
    #                 'check_in': punch_time
    #             })
    #             _logger.info(f"✅ Check-In Recorded: {employee.name} at {punch_time}")

    #         # ✅ Mark record as processed
    #         record.write({'processed': True})

    #     # ✅ Auto-close remaining check-ins after shift ends
    #     open_attendances = hr_attendance_obj.search([
    #         ('check_out', '=', False),
    #         ('check_in', '<=', now - timedelta(hours=4))  # Auto close check-ins older than 4 hours
    #     ])
    #     for open_att in open_attendances:
    #         shift_cutoff = open_att.check_in.replace(hour=12, minute=45) if open_att.check_in.hour < 16 else open_att.check_in.replace(hour=20, minute=30)
    #         auto_checkout = min(shift_cutoff, now)  # Use shift end or current time (whichever is earlier)
    #         open_att.write({'check_out': auto_checkout})
    #         _logger.info(f"⏳ Auto Check-Out Applied for {open_att.employee_id.name} at {auto_checkout}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with automatic check-in and check-out!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }















    # def action_process_attendance(self):
    #     """Process all unprocessed biometric attendance records and transfer to `hr.attendance`."""
    #     hr_attendance_obj = self.env['hr.attendance']
    #     now = fields.Datetime.now()

    #     unprocessed_attendance = self.search([('processed', '=', False)], order="punching_time asc")

    #     for record in unprocessed_attendance:
    #         employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

    #         if not employee:
    #             _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")
    #             continue

    #         atten_time = record.punching_time

    #         # Find an open check-in without check-out for this employee
    #         open_attendance = hr_attendance_obj.search([
    #             ('employee_id', '=', employee.id),
    #             ('check_out', '=', False)
    #         ], limit=1)

    #         if record.attendance_type == '0':  # ✅ Check-In
    #             if open_attendance:
    #                 # If an open check-in exists and more than 3 hours passed, auto-check-out
    #                 check_in_time = open_attendance.check_in
    #                 if atten_time >= check_in_time + timedelta(hours=3):
    #                     open_attendance.write({'check_out': check_in_time + timedelta(hours=3)})
    #                     _logger.info(f"⏳ Auto Check-Out after 3 hours for {employee.name} at {check_in_time + timedelta(hours=3)}")

    #             # Create a new Check-In
    #             hr_attendance_obj.create({
    #                 'employee_id': employee.id,
    #                 'check_in': atten_time
    #             })
    #             _logger.info(f"✅ Check-In Recorded: {employee.name} at {atten_time}")

    #         elif record.attendance_type == '1':  # ✅ Check-Out
    #             if open_attendance:
    #                 open_attendance.write({'check_out': atten_time})
    #                 _logger.info(f"✅ Check-Out Recorded: {employee.name} at {atten_time}")
    #             else:
    #                 # If no Check-In exists, create a fallback entry
    #                 hr_attendance_obj.create({
    #                     'employee_id': employee.id,
    #                     'check_in': atten_time - timedelta(minutes=1),
    #                     'check_out': atten_time
    #                 })
    #                 _logger.warning(f"⚠️ No Check-In Found! Creating a fallback entry for {employee.name}.")

    #         # ✅ Mark record as processed
    #         record.write({'processed': True})

    #     # ✅ Auto-close remaining check-ins older than 3 hours
    #     open_attendances = hr_attendance_obj.search([
    #         ('check_out', '=', False),
    #         ('check_in', '<=', now - timedelta(hours=3))
    #     ])
    #     for open_att in open_attendances:
    #         open_att.write({'check_out': open_att.check_in + timedelta(hours=3)})
    #         _logger.info(f"⏳ Auto Check-Out Applied for {open_att.employee_id.name} at {open_att.check_in + timedelta(hours=3)}")

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'message': 'Attendance processed successfully with auto check-out fix!',
    #             'type': 'success',
    #             'sticky': False
    #         }
    #     }

















# class MachineAttendance(models.Model):
#     """Intermediate table to store biometric attendance before processing."""
#     _name = 'zk.machine.attendance'
#     _description = 'Biometric Attendance Log'

#     employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
#     device_id_num = fields.Char(string="Device ID")
#     attendance_type = fields.Selection([('0', 'Check In'), ('1', 'Check Out')], string="Attendance Type")
#     punch_type = fields.Char(string="Punch Type")
#     punching_time = fields.Datetime(string="Punching Time", required=True)
#     address_id = fields.Many2one('res.partner', string="Location")
#     processed = fields.Boolean(string="Processed", default=False)

#     def action_process_attendance(self):
#         """Move validated attendance records from `zk.machine.attendance` to `hr.attendance` with auto-fix for missing check-outs."""
#         zk_attendance_obj = self.env['zk.machine.attendance']
#         hr_attendance_obj = self.env['hr.attendance']
#         now = fields.Datetime.now()

#         unprocessed_attendance = zk_attendance_obj.search([('processed', '=', False)], order="punching_time asc")

#         for record in unprocessed_attendance:
#             employee = record.employee_id
#             atten_time = record.punching_time

#             # # Find an existing open attendance (check-in without check-out)
#             # open_attendance = hr_attendance_obj.search([
#             #     ('employee_id', '=', employee.id),
#             #     ('check_out', '=', False)
#             # ], limit=1)

#             # Find the employee using device_id_num
#             employee = self.env['hr.employee'].search([('device_id_num', '=', record.device_id_num)], limit=1)

#             if employee:
#                 # Find an existing open attendance (check-in without check-out) using device_id_num
#                 open_attendance = hr_attendance_obj.search([
#                     ('employee_id', '=', employee.id),
#                     ('check_out', '=', False)
#                 ], limit=1)

#                 if record.attendance_type == '0':  # ✅ Check-In
#                     if open_attendance:
#                         # If a previous check-in exists without a check-out, auto-check-out after 3 hours
#                         check_in_time = open_attendance.check_in
#                         if atten_time >= check_in_time + timedelta(hours=3):
#                             open_attendance.write({'check_out': check_in_time + timedelta(hours=3)})
#                             _logger.info(f"⏳ Auto Check-Out after 3 hours for Employee {employee.name} at {check_in_time + timedelta(hours=3)}")

#                     # Create a new Check-In record
#                     hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})
#                     _logger.info(f"✅ Check-In Recorded: {employee.name} at {atten_time}")

#                 elif record.attendance_type == '1':  # ✅ Check-Out
#                     if open_attendance:
#                         open_attendance.write({'check_out': atten_time})
#                         _logger.info(f"✅ Check-Out Recorded: {employee.name} at {atten_time}")
#                     else:
#                         # If no previous check-in exists, create an entry with both Check-In & Check-Out
#                         hr_attendance_obj.create({
#                             'employee_id': employee.id,
#                             'check_in': atten_time - timedelta(minutes=1),
#                             'check_out': atten_time
#                         })
#                         _logger.warning(f"⚠️ No Check-In Found! Creating a fallback entry for {employee.name}.")

#                 # ✅ Mark as processed to avoid duplication
#                 record.write({'processed': True})
#             else:
#                 _logger.warning(f"⚠️ No Employee Found for Device ID: {record.device_id_num}")




#             # if record.attendance_type == '0':  # ✅ Check-In
#             #     if open_attendance:
#             #         # If a previous check-in exists without a check-out, auto-check-out after 3 hours
#             #         check_in_time = open_attendance.check_in
#             #         if atten_time >= check_in_time + timedelta(hours=3):
#             #             open_attendance.write({'check_out': check_in_time + timedelta(hours=3)})
#             #             _logger.info(f"⏳ Auto Check-Out after 3 hours for Employee {employee.name} at {check_in_time + timedelta(hours=3)}")

#             #     # Create a new Check-In record
#             #     hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})
#             #     _logger.info(f"✅ Check-In Recorded: {employee.name} at {atten_time}")

#             # elif record.attendance_type == '1':  # ✅ Check-Out
#             #     if open_attendance:
#             #         open_attendance.write({'check_out': atten_time})
#             #         _logger.info(f"✅ Check-Out Recorded: {employee.name} at {atten_time}")
#             #     else:
#             #         # If no previous check-in exists, create an entry with both check-in and check-out
#             #         hr_attendance_obj.create({
#             #             'employee_id': employee.id,
#             #             'check_in': atten_time - timedelta(minutes=1),
#             #             'check_out': atten_time
#             #         })
#             #         _logger.warning(f"⚠️ No Check-In Found! Creating a fallback entry for {employee.name}.")

#             # ✅ Mark as processed to avoid duplication
#             record.write({'processed': True})

#         # ✅ Auto-fix remaining open check-ins older than 3 hours
#         open_attendances = hr_attendance_obj.search([
#             ('check_out', '=', False),
#             ('check_in', '<=', now - timedelta(hours=3))
#         ])
#         for open_att in open_attendances:
#             open_att.write({'check_out': open_att.check_in + timedelta(hours=3)})
#             _logger.info(f"⏳ Auto Check-Out Applied for {open_att.employee_id.name} at {open_att.check_in + timedelta(hours=3)}")

#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'message': 'Attendance processed successfully with auto check-out fix!',
#                 'type': 'success',
#                 'sticky': False
#             }
#         }

    # @api.model
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
    #                 # Close the previous open attendance before starting a new one
    #                 open_attendance.write({'check_out': atten_time})

    #             # Create a new Check-In record
    #             hr_attendance_obj.create({'employee_id': employee.id, 'check_in': atten_time})

    #         elif record.attendance_type == '1':  # Check-Out
    #             if open_attendance:
    #                 open_attendance.write({'check_out': atten_time})
    #             else:
    #                 # If no Check-In exists, create a fallback record with both Check-In & Check-Out
    #                 hr_attendance_obj.create({
    #                     'employee_id': employee.id,
    #                     'check_in': atten_time,
    #                     'check_out': atten_time
    #                 })

    #         # ✅ Mark as processed so it's not duplicated next time
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

