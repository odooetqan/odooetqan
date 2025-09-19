# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models

AR_PRESENT         = 'حاضر'
AR_LATE_PRESENT    = 'متأخر'
AR_ABSENT          = 'غائب'
AR_ABSENT_EXCUSED  = 'غائب بعذر'
AR_PERMIT          = 'مستأذن'
AR_NOT_TAKEN       = 'لم يتم تحضيرهم'

class ClassGroups(models.Model):
    _inherit = "classes.groups"

    # name = fields.Char(string = "Name")
    # classe_ids = fields.One2many('classes.classe', 'group_id', string="الفصول")

class ClassClass(models.Model):
    _inherit = "classes.classe"

    # name = fields.Char(string = "Name")
    # group_id  = fields.Many2one("classes.groups", string="الشعبة/المجموعة",
                            #   )

# ------------------------------------------------------------
# Extend res.partner (FIXED: correct model name, single class)
# ------------------------------------------------------------
class ResPartnerStudent(models.Model):
    _inherit = "res.partner"

    # student_number = fields.Char(string="رقم الطالب")
    # add ondelete and remove readonly so you can clear it in UI if needed
    device_id = fields.Many2one(
        "biostar.device",
        string="الجهاز",
        ondelete="set null",
    )
# ------------------------------------------------------------
# Student Attendance
# ------------------------------------------------------------
class StudentAttendance(models.Model):
    _inherit = "student.attendance"
    _description = "Student Attendance"
    _order = "attendance_date desc, student_id"


    attendance_date = fields.Date(
        string="تاريخ الحضور", required=True, index=True,
        default=lambda self: fields.Date.context_today(self)
    )

    first_check_in = fields.Datetime(string="أول دخول (جهاز)", readonly=True)
    device_id      = fields.Many2one("biostar.device", string="الجهاز", readonly=True)

    state = fields.Selection([
        (AR_PRESENT,        "حاضر"),
        (AR_LATE_PRESENT,   "متأخر"),
        (AR_ABSENT,         "غائب"),
        (AR_ABSENT_EXCUSED, "غائب بعذر"),
        (AR_PERMIT,         "مستأذن"),
        (AR_NOT_TAKEN,      "لم يتم تحضيرهم"),
    ], string="حضور الطالب", default=AR_NOT_TAKEN, required=True, index=True)

    note       = fields.Char(string="ملاحظة")
    # on student.attendance (or whatever comodel)
    work_calendar_id = fields.Many2one('resource.calendar', string="Work Calendar", ondelete='cascade')

    _sql_constraints = [
        ('uniq_student_day', 'unique(student_id, attendance_date)',
         'تم تسجيل حضور هذا الطالب في هذا التاريخ مسبقاً.')
    ]

    def _student_status_from_checkin(self, device, date_val, first_dt):
        """Arabic status from device windows."""
        start_float = (device.start_attendance_student if device else 8.0) or 8.0
        grace       = int(device.time_to_present_late if device else 10)
        cutoff_min  = int(device.time_to_calculate_absent if device else 60)

        h = int(start_float)
        m = int(round((start_float - h) * 60))
        start_dt = fields.Datetime.to_datetime(f"{date_val} {h:02d}:{m:02d}:00")

        if not first_dt:
            cutoff = start_dt + timedelta(minutes=cutoff_min)
            return AR_ABSENT if fields.Datetime.now() >= cutoff else AR_NOT_TAKEN

        delta_min = int((first_dt - start_dt).total_seconds() // 60)
        if delta_min <= grace:
            return AR_PRESENT
        if delta_min <= cutoff_min:
            return AR_LATE_PRESENT
        return AR_ABSENT

# ------------------------------------------------------------
# BioStar User (unchanged, requires biostar.device model)
# ------------------------------------------------------------
class BiostarUser(models.Model):
    _name = "biostar.user"
    _description = "BioStar User"

    name = fields.Char(required=True)
    device_id = fields.Many2one("biostar.device", required=True, ondelete="cascade")
    biostar_user_id = fields.Char(required=True, index=True)
    card_no = fields.Char()

    employee_id = fields.Many2one(
        "hr.employee", string="Linked Employee",
        help="Link to employee (barcode should match BioStar user/card if you prefer auto)"
    )
    employee_barcode = fields.Char(related="employee_id.barcode", store=False)

    student_id = fields.Many2one(
        "res.partner", string="Linked Student",
        domain=[('student_number', '!=', False)],
        help="If set, logs can build student.attendance for this student."
    )
    student_number = fields.Char(related="student_id.student_number", store=False)