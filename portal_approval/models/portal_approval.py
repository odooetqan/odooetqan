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

    # Computed booleans based on category fields
    has_date_bool = fields.Boolean(
        string="يحتوي على التاريخ", compute="_compute_has_date", store=True, default=False
    )
    has_document_bool = fields.Boolean(
        string="يحتوي على المستند", compute="_compute_has_document", store=True, default=False
    )
    has_amount_bool = fields.Boolean(
        string="يحتوي على المبلغ", compute="_compute_has_amount", store=True, default=False
    )

    @api.depends('category_id.has_date')
    def _compute_has_date(self):
        for rec in self:
            if rec.category_id.has_date == 'required':
                rec.has_date_bool = True
            else:
                rec.has_date_bool = False


    @api.depends('category_id.has_document')
    def _compute_has_document(self):
        for rec in self:
            if rec.category_id.has_document == 'required':
                rec.has_document_bool = True
            else:
                rec.has_document_bool = False


    @api.depends('category_id.has_amount')
    def _compute_has_amount(self):
        for rec in self:
            if rec.category_id.has_amount == 'required':
                rec.has_amount_bool = True
            else:
                rec.has_amount_bool = False