class HRDiscountCorrection(models.Model):
    _name = 'hr.discount.correction'
    _description = 'Salary Deduction Correction Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    discount_id = fields.Many2one('hr.discount', string='Discount Record', required=True)
    note = fields.Text(string="Correction Reason")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', tracking=True)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.discount_id.write({'deducted_amount': 0, 'state': 'corrected'})
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})
