from odoo import models, fields, api

class PortalApprovalCategory(models.Model):
    _inherit = "approval.category"

    has_date = fields.Boolean(string="يحتوي على التاريخ", default=False)
    has_document = fields.Boolean(string="يحتوي على المستند", default=False)
    has_amount = fields.Boolean(string="يحتوي على المبلغ", default=False)
    is_active = fields.Boolean(string="Is Active", default=False)


class PortalApprovalRequest(models.Model):
    _inherit = "approval.request"

    is_active = fields.Boolean(string="Is Active", default=False)
    date_from = fields.Datetime(string="من")
    date_to = fields.Datetime(string="إلى")
    document = fields.Binary(string="المستند")
    amount = fields.Float(string="المبلغ")

    # Related fields to category
    has_date = fields.Boolean(related='category_id.has_date', string="يحتوي على التاريخ", store=True)
    has_document = fields.Boolean(related='category_id.has_document', string="يحتوي على المستند", store=True)
    has_amount = fields.Boolean(related='category_id.has_amount', string="يحتوي على المبلغ", store=True)
