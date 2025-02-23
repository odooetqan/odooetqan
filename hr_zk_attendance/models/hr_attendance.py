class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    late_minutes = fields.Float(string="Lateness (Minutes)", compute="_compute_lateness", store=True)
    overtime_minutes = fields.Float(string="Overtime (Minutes)", compute="_compute_overtime", store=True)

    @api.depends('employee_id', 'check_in')
    def _compute_lateness(self):
        """Calculate lateness in minutes based on scheduled shift start time."""
        for record in self:
            if not record.employee_id or not record.check_in:
                record.late_minutes = 0
                continue

            shift = record.employee_id.resource_calendar_id
            if not shift:
                record.late_minutes = 0
                continue

            check_in_time = record.check_in
            punch_date = check_in_time.date()
            ksa_tz = timezone('Asia/Riyadh')  # Adjust based on your timezone

            for att in shift.attendance_ids:
                if att.dayofweek == str(punch_date.weekday()):
                    shift_start = datetime.combine(punch_date, datetime.min.time()).replace(
                        hour=int(att.hour_from), minute=int((att.hour_from % 1) * 60)
                    )
                    shift_start_utc = ksa_tz.localize(shift_start).astimezone(utc)

                    late_duration = (check_in_time.replace(tzinfo=None) - shift_start_utc.replace(tzinfo=None)).total_seconds() / 60
                    record.late_minutes = max(0, late_duration)  # Ensure non-negative value

    @api.depends('employee_id', 'check_out')
    def _compute_overtime(self):
        """Calculate overtime in minutes based on scheduled shift end time."""
        for record in self:
            if not record.employee_id or not record.check_out:
                record.overtime_minutes = 0
                continue

            shift = record.employee_id.resource_calendar_id
            if not shift:
                record.overtime_minutes = 0
                continue

            check_out_time = record.check_out
            punch_date = check_out_time.date()
            ksa_tz = timezone('Asia/Riyadh')

            for att in shift.attendance_ids:
                if att.dayofweek == str(punch_date.weekday()):
                    shift_end = datetime.combine(punch_date, datetime.min.time()).replace(
                        hour=int(att.hour_to), minute=int((att.hour_to % 1) * 60)
                    )
                    shift_end_utc = ksa_tz.localize(shift_end).astimezone(utc)

                    overtime_duration = (check_out_time.replace(tzinfo=None) - shift_end_utc.replace(tzinfo=None)).total_seconds() / 60
                    record.overtime_minutes = max(0, overtime_duration)
