from odoo import models, fields, api
from odoo import models, fields, api

class PortalApprovalCategory(models.Model):
    _inherit = "approval.category"

    # Add custom fields to the approval.category model
    has_date = fields.Boolean(string="يحتوي على التاريخ")
    has_document = fields.Boolean(string="يحتوي على المستند")
    has_amount = fields.Boolean(string="يحتوي على المبلغ")


class PortalApprovalRequest(models.Model):
    _inherit = "approval.request"

    # Extend approval request with additional fields to be filled by the portal
    date_from = fields.Datetime(string="من")
    date_to = fields.Datetime(string="إلى")
    document = fields.Binary(string="المستند")
    amount = fields.Float(string="المبلغ")


class PortalApproval(models.Model):
    _inherit = "hr.leave.type"

    overtime_deductible = fields.Boolean(string="Overtime Deductible", default=False)


class HrLoan(models.Model):
    _inherit = 'hr.loan'
