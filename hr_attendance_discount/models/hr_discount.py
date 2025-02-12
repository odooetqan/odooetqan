from odoo import models, fields, api

class HRDiscount(models.Model):
    _name = 'hr.discount'
    _description = 'Salary Deduction for Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Enables chatter and approvals

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date(string="Date", required=True)
    shift_start = fields.Datetime(string="Shift Start")
    shift_end = fields.Datetime(string="Shift End")
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")

    late_minutes = fields.Integer(string="Late Minutes")
    early_leave_minutes = fields.Integer(string="Early Leave Minutes")
    absent = fields.Boolean(string="Absent", default=False)

    daily_salary = fields.Float(string="Daily Salary")
    hourly_salary = fields.Float(string="Hourly Salary")
    deducted_amount = fields.Float(string="Deduction Amount", compute="_compute_deduction", store=True)

    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('corrected', 'Corrected'),
    ], string="Status", default='pending', tracking=True)

    @api.depends('late_minutes', 'early_leave_minutes', 'daily_salary', 'hourly_salary', 'absent')
    def _compute_deduction(self):
        """ Calculate deduction based on late and absent minutes """
        for record in self:
            if record.absent:
                record.deducted_amount = record.daily_salary
            else:
                deduction = (record.late_minutes + record.early_leave_minutes) * (record.hourly_salary / 60)
                record.deducted_amount = deduction
