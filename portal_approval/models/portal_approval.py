from odoo import models, fields, api

class PortalApprovalCategory(models.Model):
    _inherit = "approval.category"

    has_date = fields.Selection(
                                string="يحتوي على التاريخ",
                                selection_add=[
                                    ("required", "Required"),
                                    ("optional", "Optional"),
                                    ("no", "None"),
                                ],
                                default="no",  # ✅ Correct: Set a valid default value
                            )
    has_document = fields.Selection(
                                string="يحتوي على المستند",
                                selection_add=[
                                    ("required", "Required"),
                                    ("optional", "Optional"),
                                    ("no", "None"),
                                ],
                                default="no",  # ✅ Correct: Set a valid default value
                            )
    has_amount = fields.Selection(
                                string="يحتوي على المبلغ",
                                selection_add=[
                                    ("required", "Required"),
                                    ("optional", "Optional"),
                                    ("no", "None"),
                                ],
                                default="no",  # ✅ Correct: Set a valid default value
                            )
    # is_active = fields.Boolean(string="Is Active", default=False)


class PortalApprovalRequest(models.Model):
    _inherit = "approval.request"

    # is_active = fields.Boolean(string="Is Active", default=False)
    date_from = fields.Datetime(string="من")
    date_to = fields.Datetime(string="إلى")
    document = fields.Binary(string="المستند")
    amount = fields.Float(string="المبلغ")

    # Related fields to category
    has_date = fields.Selection(related='category_id.has_date', string="يحتوي على التاريخ", store=True)
    has_document = fields.Selection(related='category_id.has_document', string="يحتوي على المستند", store=True)
    has_amount = fields.Selection(related='category_id.has_amount', string="يحتوي على المبلغ", store=True)
