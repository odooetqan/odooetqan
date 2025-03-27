from odoo import models, fields, api


class PortalApprovalCategory(models.Model):
    _inherit = "approval.category"

    has_date = fields.Selection(
        selection=[
            ("required", "Required"),
            ("optional", "Optional"),
            ("no", "None"),
        ],
        string="يحتوي على التاريخ",
        default="no",
    )
    has_document = fields.Selection(
        selection=[
            ("required", "Required"),
            ("optional", "Optional"),
            ("no", "None"),
        ],
        string="يحتوي على المستند",
        default="no",
    )
    has_amount = fields.Selection(
        selection=[
            ("required", "Required"),
            ("optional", "Optional"),
            ("no", "None"),
        ],
        string="يحتوي على المبلغ",
        default="no",
    )


class PortalApprovalRequest(models.Model):
    _inherit = "approval.request"

    description = fields.Text(string="الوصف")
    date_from = fields.Datetime(string="من")
    date_to = fields.Datetime(string="إلى")
    document = fields.Binary(string="المستند")
    amount = fields.Float(string="المبلغ")

    # Related fields to category
    has_date = fields.Selection(related='category_id.has_date', string="يحتوي على التاريخ", store=True)
    has_document = fields.Selection(related='category_id.has_document', string="يحتوي على المستند", store=True)
    has_amount = fields.Selection(related='category_id.has_amount', string="يحتوي على المبلغ", store=True)
