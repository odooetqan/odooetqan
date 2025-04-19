from odoo import models, fields, api

class HRDiduction(models.Model):
    _name = 'hr.diduction'
    _description = 'Salary Deduction for Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Enables chatter and approvals

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date(string="Date", required=True)
    shift_start = fields.Datetime(string="Shift Start")
    shift_end = fields.Datetime(string="Shift End")
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    
    @api.depends('employee_id', 'date')
    def _compute_check_times(self):
        for rec in self:
            rec.check_in = False
            rec.check_out = False
            if rec.employee_id and rec.date:
                start_of_day = datetime.combine(rec.date, datetime.min.time())
                end_of_day = datetime.combine(rec.date, datetime.max.time())

                # Find the attendance for the employee on that day
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('check_in', '>=', start_of_day),
                    ('check_in', '<=', end_of_day)
                ], order='check_in asc')

                if attendances:
                    # Earliest check_in
                    rec.check_in = attendances[0].check_in
                    # Latest check_out (if available)
                    check_outs = [att.check_out for att in attendances if att.check_out]
                    if check_outs:
                        rec.check_out = max(check_outs)

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
