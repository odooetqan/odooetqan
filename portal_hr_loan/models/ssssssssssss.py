# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date

# from odoo.exceptions import Warning, UserError
from odoo.exceptions import UserError


class Partners(models.Model):
    _inherit = "res.partner"

    student_id = fields.Many2one("student.student")
    guardian_id = fields.Many2one("student.guardian")

class Orders(models.Model):
    _inherit = "sale.order"

    student_id = fields.Many2one(related="partner_id.student_id")#"student.student", compute="_compute_students")
    guardian_id = fields.Many2one(related="student_id.guardian_id")#"student.student", compute="_compute_students")

class AccountMove(models.Model):
    _inherit = "account.move"

    student_id = fields.Many2one(related="partner_id.student_id")#"student.student", compute="_compute_students")
    guardian_id = fields.Many2one(related="student_id.guardian_id")#"student.student", compute="_compute_students")


class StudentStudent(models.Model):
    _name = "student.student"
    _description = "Students Model"
    # _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "id desc"

    number = fields.Char(
        string="Student Number", index=True, readonly=True, tracking=True, Default="NEW"
    )
    family_number = fields.Char(related="guardian_id.number")  # ()
    family_name = fields.Char(related="guardian_id.name")
    name2 = fields.Char(
        string="Student Number.",
        index=True,
        readonly=True,
        tracking=True,
        Default="NEW",
        compute="student_name2",
    )
    number2 = fields.Char(
        string="Number",
        index=True,
        readonly=True,
        tracking=True,
        Default="NEW",
        compute="student_name2",
    )
    name = fields.Char(string="Student Name", index=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("blocked", "Blocked"),
            ("in_active", "In Active"),
        ],
        default="draft",
        string="Student State",
        tracking=True,
    )

    class_id = fields.Many2one(
        "classes", string="Education Class", required=True, copy=True
    )
    stage_id = fields.Many2one(
        "stages",
        string="Stage",
        related="class_id.stage_id",
        tracking=True,
        required=True,
    )
    section_id = fields.Many2one(
        "sections",
        string="Section",
        related="class_id.section_id",
        tracking=True,
        required=True,
    )
    track_id = fields.Many2one(
        "tracks",
        string="Track",
        tracking=True,
        related="class_id.track_id",
        required=True,
    )
    secondary_major = fields.Many2one(
        "secondry.majors", string="Secondary Major", tracking=True
    )
    ex_school = fields.Many2one(
        "ex.schools", string="Ex School", required=True, copy=True
    )
    current_year = fields.Many2one("years", string="Current Year", copy=True)
    previous_year = fields.Many2one(
        "years", string="Previous Year", required=True, copy=True
    )

    active = fields.Boolean(default=True)
    gender = fields.Many2one(
        "gender", string="Gender", required=True, copy=True, tracking=True
    )
    nationality = fields.Many2one(
        "res.country", string="Nationality", required=True, copy=True, tracking=True
    )
    id_type = fields.Many2one(
        "id.type", string="ID Type", required=True, copy=True, tracking=True
    )
    id_number = fields.Char(string="ID Number", required=True, copy=True, tracking=True)
    tage = fields.Many2one(
        "res.partner.category", string="Tage", copy=True, tracking=True
    )
    birth_date = fields.Date(string="Birth Date")
    hijri_date = fields.Date(string="Hijri Date")
    reason = fields.Many2one("dropoff.reasons", string="Reason")
    sibling_discount = fields.Many2one("discount.type", string="Sibling Discount")
    student_discount = fields.Many2one("discounts", string="Student Discount")
    sale_order_ids = fields.Many2many("sale.order", compute="_compute_order")
    qutetions_ids = fields.Many2many("sale.order", compute="_compute_order")
    qutetions_ids = fields.Many2many("sale.order", compute="_compute_order")
    qutetion_ids = fields.Many2many("sale.order", compute="_compute_order")
    
    # Rename the following fields to have unique names
    invoice_line_ids = fields.One2many(
        "account.move.line", "partner_id", string="Invoices Items"
    )
    
    currency_id = fields.Many2one('res.currency', string='Currency', related='partner_id.currency_id')
    
    #----------------------------
    invoice_ids = fields.Many2many(comodel_name='account.move', compute='_compute_invoices', string='Invoices', readonly=True)
    invoices = fields.Many2many(comodel_name='account.move', compute='_compute_invoices', string='Invoices', readonly=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    total_remaining_amount = fields.Float(string='Total Remaining Amount', compute='_compute_invoice_count')
    
    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for student in self:
            student.invoice_count = len(student.invoice_ids)

    def action_student_invoice_count(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Invoices Count',
            'res_model': 'account.move',
            'domain': [('partner_id', '=', self.partner_id.id),('move_type', '=', 'out_invoice')],
            'view_mode':'tree,form',
            'target': 'current',
    
        }

    def _compute_invoices(self):
        for student in self:
            invoices = self.env['account.move'].search([
                        ('partner_id', '=', student.partner_id.id),
                        ('move_type', '=', 'out_invoice')  # Optional: Filter for sales invoices only
                    ])
            
            student.invoices = invoices
            student.invoice_ids = invoices
            student.total_remaining_amount = sum(invoice.amount_residual for invoice in invoices)
#-------------------------------------------------------------------------------------------------------------------------------

    order_count = fields.Integer(string="Order Count", compute="_compute_order_count")
    
    @api.depends("questions_ids")
    def _compute_order_count(self):
        for student in self:
            student.order_count = len(student.questions_ids)
    
    def action_order_students(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Orders",
            "res_model": "sale.order",
            "domain": [("partner_id", "=", self.partner_id.id)],
            "view_mode": "tree,form",
            "target": "current",
    }
    
    # def _compute_order(self):
    #     for student in self:
    #         orders = self.env['sale.order'].search([
    #             ('partner_id', '=', student.partner_id.id),
    #         ])
            
    #         student.questions_ids = orders
        
    def _compute_order(self):
        for student in self:            
            # print("Student Partner ID:", student.partner_id.id)
            orders = self.env['sale.order'].search([
                ('partner_id', '=', student.partner_id.id),
            ])
            # print("Number of Orders:", len(orders))
            student.questions_ids = orders
            student.question_ids = orders
            student.sale_order_ids = orders

    def unlink(self):
        for rec in self:
            if rec.state not in ("draft", "cancel", "blocked"):
                raise UserError(
                    "You cannot delete a student that is not in draft, cancel, or blocked state."
                )
        return super(StudentStudent, self).unlink()

    know_us = fields.Many2one(
        "know.us",
        required=True,
        copy=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=False,
        copy=True,
        tracking=True,
    )
    mobile = fields.Char(
        "Mobile",
        required=True,
        copy=True,
        tracking=True,
    )
    mobile2 = fields.Char(
        "Mobile2",
        required=True,
        copy=True,
        tracking=True,
    )
    email = fields.Char(
        "Email",
        required=True,
        copy=True,
        tracking=True,
    )
    guardian_id = fields.Many2one("student.guardian", string="Guardian", required=True)
    student_date = fields.Date(
        string="Student Date",
        default=fields.Date.today(),
        required=True,
        copy=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.user.company_id,
        required=True,
        copy=True,
    )
    date_end = fields.Date(
        string="Student Deadline",
        help="Last date for the student to be needed",
        copy=True,
    )
    date_done = fields.Date(
        string="Date Done",
        help="Date of Completion of student Student",
    )
    confirm_date = fields.Date(
        string="Confirmed Date",
        copy=False,
    )
    userblocked_date = fields.Date(
        string="Blocked Date",
        readonly=True,
        copy=False,
    )
    employee_confirm_id = fields.Many2one(
        "hr.employee",
        string="Confirmed by",
        readonly=True,
        copy=False,
    )
    blocked_employee_id = fields.Many2one(
        "hr.employee",
        string="Blocked by",
        readonly=True,
        copy=False,
    )

    street = fields.Char(related='partner_id.street')
    street2 = fields.Char(related='partner_id.street2')
    city = fields.Char(related='partner_id.city')
    country_id = fields.Many2one('res.country',related='partner_id.country_id')


    # seq
    @api.model
    def create(self, vals):
        if vals.get("number", _("New")) == _("New") and vals.get(
            "guardian_id"
        ):  # adding add....
            guardian = self.env["student.guardian"].browse(
                vals["guardian_id"]
            )  # addtional
            if guardian:
                vals["number"] = guardian.number or _("New")
            vals["number"] = self.env["ir.sequence"].next_by_code(
                "student.student.seq"
            ) or _("New")
        res = super(StudentStudent, self).create(vals)
        return res

    def student_confirm(self):
        for rec in self:
            # manager_mail_template = self.env.ref('reg.email_confirm_school_reg_base')
            rec.employee_confirm_id = self.env["hr.employee"].search(
                [("user_id", "=", self.env.uid)], limit=1
            )
            rec.confirm_date = fields.Date.today()
            rec.state = "active"

    @api.depends("name", "number", "partner_id")
    def student_name2(self):
        for rec in self:
            rec.name2 = ""
            rec.number2 = ""
            number = rec.number
            partner = self.env["res.partner"].sudo().browse(rec.partner_id.id)
            if not partner.student_id:
                partner.write({"student_id": rec.id}) 

    def student_blocked(self):
        for rec in self:
            rec.state = "blocked"
            rec.blocked_employee_id = self.env["hr.employee"].search(
                [("user_id", "=", self.env.uid)], limit=1
            )
            rec.userblocked_date = fields.Date.today()

    def reset_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_archive(self):
        for rec in self:
            rec.active = False

    # Add a field to store this student's unique sequence number
    student_seq = fields.Char(string="Student Sequence", readonly=True)
    student_number = fields.Char(string="Student Number", readonly=True)

    @api.model
    def create(self, vals):
        guardian_id = vals.get("guardian_id")
        partner_vals = {
            "student_id": vals.get("id"),
            "name": vals.get("name"),
            "mobile": vals.get("mobile"),
            "email": vals.get("email"),
        }

        if guardian_id:
            guardian = self.env["student.guardian"].browse(guardian_id)

            # Create the partner with the provided values
            partner = self.env["res.partner"].create(partner_vals)
            partner.write({"student_id": self.id})
            # Set the partner on the student
            vals["partner_id"] = partner.id

            # Increment the guardian's last student sequence
            guardian.write({"last_student_seq": guardian.last_student_seq + 1})

            # Assign the new sequence to the student
            vals["student_seq"] = str(guardian.number) + str(guardian.last_student_seq)
            vals["student_number"] = str(guardian.number) + str(
                guardian.last_student_seq
            )

        student = super(StudentStudent, self).create(vals)
        return student
 
    @api.constrains("name")
    def _check_name(self):
        partner_rec = self.env["student.student"].search(
            [("name", "=", self.name), ("id", "!=", self.id)]
        )
        if partner_rec:
            raise ValueError(_("مكرر! الاسم موجود من قبل ."))

    @api.constrains("mobile")
    def _check_mobile(self):
        partner_rec = self.env["student.student"].search(
            [("mobile", "=", self.mobile), ("id", "!=", self.id)]
        )
        if partner_rec:
            raise ValueError(_("مكرر! هذا الرقم موجود "))

    @api.constrains("id_number")
    def _check_id_number(self):
        partner_rec = self.env["student.student"].search(
            [("id_number", "=", self.id_number), ("id", "!=", self.id)]
        )
        if partner_rec:
            raise ValueError(_("مكرر! هذا الرقم موجود "))
