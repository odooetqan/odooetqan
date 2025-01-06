 # -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date

# from odoo.exceptions import Warning, UserError
from odoo.exceptions import UserError

class Partners(models.Model):
    _inherit = "res.partner"
 
    # analytic_account_id = fields.Many2one('account.analytic.account', string='Anyltic Account')
    student_id = fields.Many2one("student.student", compute="_compute_students")
    guardian_id = fields.Many2one("student.guardian", compute="_compute_guardian")
    district = fields.Char(string="Discrit")
    # district = fields.Char(string="District")

    @api.depends('is_company', 'child_ids', 'child_ids.student_id')
    def _compute_students(self):
        for rec in self:
            student = self.env['student.student'].search([('partner_id', '=', rec.id)], limit=1)
            rec.student_id = student

    # If guardian_id needs to be computed as well, here's an example:
    @api.depends('is_company', 'child_ids', 'child_ids.guardian_id')
    def _compute_guardian(self):
        for rec in self:
            student = self.env['student.student'].search([('partner_id', '=', rec.id)], limit=1)
            rec.student_id = student
            if student:
                rec.guardian_id = student.guardian_id
            else:
                guardian = self.env['student.guardian'].search([('partner_id', '=', rec.id)], limit=1)                    
                rec.guardian_id = guardian
class resPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    student_id = fields.Many2one('student.student')
    guardian_id = fields.Many2one('student.guardian')
    
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

    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']      # odoo11
    _order = 'id desc'
     
    def get_default_student_status(self):
            default_student_status = 'new'
            return default_student_status
    student_status = fields.payment_method = fields.Selection(
        selection=[
            ('new', 'New'),
            ('renew', 'Re-New'),
            ('under_regesteration', 'Under Registeration'),
            ],
        string='Student Status', default = get_default_student_status, index=True, tracking=True,)
    
    def get_default_type_id_number(self):
            default_auType = 'هوية وطنية'
            return default_auType

    contact_id_type = fields.Selection(selection=[
            ('هوية وطنية', 'هوية وطنية'),
            ('إقامة نظامية', 'إقامة نظامية'),
            ('جواز سفر', 'جواز سفر'),
            ('كرت العائلة', 'كرت العائلة'),
            ('تأشيرة زيارة', 'تأشيرة زيارة'),
            ('وثيقة', 'وثيقة'),
            ('سجل تجاري', 'سجل تجاري'),
    ], string=' نوع الهوية', default=get_default_type_id_number)

    number = fields.Char(string="Student Number", index=True, readonly=True, tracking=True, Default="NEW"    )
    family_number = fields.Char(related="guardian_id.number")  # ()
    family_name = fields.Char(related="guardian_id.name")
    name2 = fields.Char(string="Student Number.",index=True,readonly=True,tracking=True,Default="NEW",compute="student_name2",    )
    number2 = fields.Char(string="Number",index=True,readonly=True,tracking=True,Default="NEW",compute="student_name2",    )
    name = fields.Char(string="Student Name", index=True, tracking=True)
    state = fields.Selection([    ("draft", "Draft"),    ("active", "Active"),    ("blocked", "Blocked"),    ("in_active", "In Active"),],default="draft",string="Student State",tracking=True,)
    class_id = fields.Many2one("classes", string="Education Class", required=True, copy=True    )
    product_id = fields.Many2one("product.template", related="class_id.product_id", string="Product")
    stage_id = fields.Many2one("stages",string="Stage",related="class_id.stage_id",tracking=True,required=True, )
    is_secondary = fields.Boolean(related = 'stage_id.is_secondary')
    section_id = fields.Many2one("sections",string="Section",related="class_id.section_id",tracking=True,required=True, )
    track_id = fields.Many2one("tracks",string="Track",tracking=True,related="class_id.track_id",required=True,)
    secondary_major = fields.Many2one("secondry.majors", string="Secondary Major", tracking=True)
    ex_school = fields.Many2one("ex.schools", string="Ex School", copy=True, tracking=True)
    current_year = fields.Many2one("years", string="Current Year", required=True, copy=True, tracking=True)
    previous_year = fields.Many2one("years", string="Previous Year", copy=True)
    company_current_year = fields.Integer(related="company_id.current_year") 
    active = fields.Boolean(default=True)
    gender = fields.Many2one("gender", string="Gender", required=True, copy=True, tracking=True)
    nationality = fields.Many2one("res.country", string="Nationality", required=True, copy=True, tracking=True)
    id_type = fields.Many2one("id.type", string="ID Type", required=True, copy=True, tracking=True)
    id_number = fields.Char(string="ID Number", required=True, copy=True, tracking=True)

    tax_type = fields.Many2one('account.tax', string="Tax Type")


 

    @api.onchange('id_number')
    def _onchange_id_number(self):
        zero_rate_tax = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', 0)], limit=1)
        standard_rate_tax = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', 15)], limit=1)
        if self.id_number and self.id_number.startswith('1'):
            self.tax_type = zero_rate_tax
        else:
            self.tax_type = standard_rate_tax


 
    tage = fields.Many2many("res.partner.category", "student_id",string="Tage", copy=True, tracking=True)
    birth_date = fields.Date(string="Birth Date")
    hijri_date = fields.Date(string="Hijri Date")
    reason = fields.Many2one("dropoff.reasons", string="Reason")

    student_discount = fields.One2many("discounts","student_id", string="Student Discount")
    discount = fields.Float(compute="_compute_total_discounts", string="Total Discounts")

    @api.depends("student_discount")
    def _compute_total_discounts(self):
        for rec in self:
            total_discount = 0.0
            if rec.student_discount:
                for discount in rec.student_discount:
                    total_discount += discount.ratio
            rec.discount = total_discount


 
    # @api.depends("student_discount")
    # def _compute_total_discounts(self):
    #     for rec in self:
    #         if rec.student_discount:
    #             rec.discount = rec.student_discount.ratio
    #         else:
    #             rec.discount = 0.0
  
    # discount = fields.Integer(string="Discount", compute="_compute_discount")
    # def _compute_discount(self):
    #     discounts = self.env['discounts'].search([('student_id', '=', id)])
    #     for record in discounts:
    #         discount += record.ratio
    #     self.discount = discount
    sibling_discount = fields.Many2one("discount.type", string="Sibling Discount")
    # student_discount = fields.Many2one("discounts", string="Student Discount")
    # Rename the following fields to have unique names
    invoice_line_ids = fields.One2many("account.move.line", "partner_id", string="Invoices Items")
    #----------------------------------
    promissory_ids = fields.Many2many(comodel_name='promissory.note', compute='_compute_promissory', string='Promissory',readonly=True)#, ondelete='cascade'
    def _compute_promissory(self):
        for record in self:
            student_id = record.id
            promissorys = self.env['promissory.note'].search([('student_id', '=', student_id)])
            record.promissory_ids = promissorys or False
                
    # promissory_count = fields.Integer(string='Promissory Count', compute='_compute_promissory_count')
    # @api.depends('promissory_ids')
    # def _compute_promissory_count(self):
    #     for promissory in self:
    #         promissorys = promissory.promissory_ids
    #         if promissorys:
    #             promissory.promissory_count = len(promissory.promissory_ids)
    #         else:
    #             contract.promissory_count = 0
    

    # promissory_ids = fields.One2many('promissory.note', 'student_id', string='Promissory Notes', ondelete='cascade')
  
    @api.model
    def unlink(self):
        for student in self:
            # Delete related promissory note records
            promissory_notes = self.env['promissory.note']#.search([('student_id', '=', student.id)])
            promissory_notes.unlink()
        # return super(StudentStudent, self).unlink()
        

    promissory_count = fields.Integer(string="Promissory Count", compute="_compute_promissory_count")
    
    @api.depends("promissory_ids")
    def _compute_promissory_count(self):
        for record in self:
            record.promissory_count = len(record.promissory_ids)
    

    
    def action_student_promissory_count(self):
        
        return{
            'type': 'ir.actions.act_window',
            'name': 'Promissory Count',
            'res_model': 'promissory.note',
            'domain': [('student_id', '=', self.id)],
            'view_mode':'tree,form',
            'target': 'current',
    
        }

#----------------------------------
    currency_id = fields.Many2one('res.currency', string='Currency', related='partner_id.currency_id')
    contract_ids = fields.Many2many(comodel_name='student.student.contract', compute='_compute_contracts', string='Contracts',readonly=True)
    def _compute_contracts(self):
        for record in self:
            student_id = record.id
            contracts = self.env['student.student.contract'].search([('student_id', '=', student_id)])
            record.contract_ids = contracts or False

    
    contract_count = fields.Integer(string="Promissory Count", compute="_compute_contract_count")
    
    @api.depends("contract_ids")
    def _compute_contract_count(self):
        for record in self:
            record.contract_count = len(record.contract_ids)

    def action_student_contract_count(self):
           return{
               'type': 'ir.actions.act_window',
               'name': 'Contract Count',
               'res_model': 'student.student.contract',
               'domain': [('student_id', '=', self.id)],
               'view_mode':'tree,form',
               'target': 'current',
       
           }

                
    #----------------------------
    invoice_ids = fields.Many2many(comodel_name='account.move', compute='_compute_invoices', string='Invoices', readonly=True)
    invoices = fields.Many2many(comodel_name='account.move', compute='_compute_invoices', string='Invoices', readonly=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    total_remaining_amount = fields.Float(string='Total Remaining Amount', compute='_compute_invoices')
    
    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

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
        for record in self:
            invoices = self.env['account.move'].search([
                        ('partner_id', '=', record.partner_id.id),
                        ('move_type', '=', 'out_invoice')  # Optional: Filter for sales invoices only
                    ])
            if invoices:
                record.invoices = invoices
                record.invoice_ids = invoices
                record.total_remaining_amount = sum(invoice.amount_residual for invoice in invoices)
            else:
                record.invoices = False
                record.invoice_ids = False
                record.total_remaining_amount = 0.0
#-------------------------------------------------------------------------------------------------------------------------------

    order_count = fields.Integer(string="Order Count", compute="_compute_order_count")
    
    @api.depends("sale_order_ids")
    def _compute_order_count(self):
        for record in self:
            record.order_count = len(record.sale_order_ids)

    def action_order_students(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Orders",
            "res_model": "sale.order",
            "domain": [("partner_id", "=", self.partner_id.id), ("state", "=", "sale")],
            "view_mode": "tree,form",
            "target": "current",
        }

    pricelist_id = fields.Many2one('product.pricelist')
    def action_order_students_form(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Orders",
            "res_model": "sale.order",
            # "domain": [("partner_id", "=", self.partner_id.id)],
            "view_mode": "form,tree",
            "target": "current",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_order_line": [(0, 0, {
                               
                    'name' : self.product_id.name,
                    'product_id' : self.product_id.id,
                    'product_uom' : self.product_id.uom_id.id,
                    'product_uom_qty' : 1


                 
                 # "product_id": self.product_id.id, 
                 # "discount": self.discount
                })],
                "form_view_ref": "sale.view_order_form",
                "tree_view_ref": "sale.view_order_tree",
            },
        }

 
           
    def action_contract_students_form(self):
        return {
            "type": "ir.actions.act_window",
            "name": "contract",
            "res_model": "student.student.contract",
            # "domain": [("partner_id", "=", self.partner_id.id)],
            "view_mode": "form,tree",
            "target": "current",
            "context": {
                "default_student_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

        
    def action_promissory_students_form(self):
        return {
            "type": "ir.actions.act_window",
            "name": "contract",
            "res_model": "promissory.note",
            # "domain": [("partner_id", "=", self.partner_id.id)],
            "view_mode": "form,tree",
            "target": "current",
            "context": {
                "default_student_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

 
# , "product_uom_qty": 1, "product_uom": self.product_id.uom_id.id
 
    # def action_order_students_form(self):
    #     # pricelist_id = self.pricelist_id or False
    #     return {
    #         "type": "ir.actions.act_window",
    #         "name": "Orders",
    #         "res_model": "sale.order",
    #         "domain": [("partner_id", "=", self.partner_id.id)],#, ("state", "!=", "sale")
    #         "view_mode": "form,tree",
    #         "target": "current",
    #         "context": {
    #             "default_partner_id": self.partner_id.id,
    #             # "default_pricelist_id": pricelist_id.id,
    #             "default_order_line": [
    #                 (0, 0, {
    #                     "product_id": self.product_id.id,
    #                     "product_uom_qty": 1,
    #                     "product_uom": self.product_id.uom_id.id,
    #                     "discount": self.discount,                     
    #                 }),
    #             ],
    #         },
    #     }


    qutation_count = fields.Integer(string="Qutation Count", compute="_compute_qutation_count")

    @api.depends("qutetions_ids")
    def _compute_qutation_count(self):
        for record in self:
            record.qutation_count = len(record.qutetions_ids)

 
    def action_qutation_students(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Orders",
            "res_model": "sale.order",
            "domain": [("partner_id", "=", self.partner_id.id), ("state", "!=", "sale")],
            "view_mode": "tree,form",
            "target": "current",
        }
    


    sale_order_ids = fields.Many2many("sale.order", compute="compute_order")
    qutetions_ids = fields.Many2many("sale.order", compute="compute_qutations")


    def compute_order(self):
        for record in self:            
            orders = self.env['sale.order'].search([
                ('partner_id', '=', record.partner_id.id),('state', '=', 'sale')
            ])
            record.sale_order_ids = orders


    def compute_qutations(self):
        for record in self:            
            orders = self.env['sale.order'].search([
                ('partner_id', '=', record.partner_id.id),('state', '!=', 'sale')
            ])
            record.qutetions_ids = orders

    
    def unlink(self):
        for record in self:
            # Delete related promissory note records
            promissory_notes = self.env['promissory.note'].search([('student_id', '=', record.student_id.id)])
            promissory_notes.unlink()
            if rec.state not in ("draft", "cancel", "blocked"):
                raise UserError(
                    "You cannot delete a student that is not in draft, cancel, or blocked state."
                )
        # return super(StudentStudent, self).unlink()

    know_us = fields.Many2one("know.us",required=True,copy=True,tracking=True,    )
    partner_id = fields.Many2one("res.partner",required=False,copy=True,tracking=True,    )
    mobile = fields.Char("Mobile",related="guardian_id.mobile",tracking=True,    )
    mobile2 = fields.Char("Mobile2",related="guardian_id.mobile2",tracking=True,    )
    email = fields.Char("Email",related="guardian_id.email", copy=True,tracking=True,    )
    guardian_id = fields.Many2one("student.guardian", string="Guardian", required=True)
    student_date = fields.Date(string="Student Date",default=fields.Date.today(),required=True,copy=True,tracking=True,    )
    company_id = fields.Many2one("res.company",string="Company",default=lambda self: self.env.user.company_id,required=True,copy=True,    )
    date_end = fields.Date(string="Student Deadline",help="Last date for the student to be needed",copy=True,    )
    date_done = fields.Date(string="Date Done",help="Date of Completion of student Student",    )
    confirm_date = fields.Date(string="Confirmed Date",copy=False,    )
    userblocked_date = fields.Date(string="Blocked Date",readonly=True,copy=False,    )
    employee_confirm_id = fields.Many2one("hr.employee",string="Confirmed by",readonly=True,copy=False,    )
    blocked_employee_id = fields.Many2one("hr.employee",string="Blocked by",readonly=True,copy=False,     )
    street = fields.Char(related='partner_id.street')
    street2 = fields.Char(related='partner_id.street2')
    city = fields.Char(related='partner_id.city')
    is_secondary = fields.Boolean(related='stage_id.is_secondary')
    country_id = fields.Many2one('res.country',related='partner_id.country_id')
    
    @api.onchange("guardian_id")
    def onchange_guardian_id(self):
        if self.guardian_id:
            self.mobile = self.guardian_id.mobile 
            self.name = self.name + ' ' + self.guardian_id.name


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

        if not vals.get("mobile"):
            vals["mobile"] = self.env.context.get("default_mobile", "000-000-0000")
            
        guardian_id = vals.get("guardian_id")
        name = vals.get("name")
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
            vals["student_number"] = str(guardian.number) + str(guardian.last_student_seq)
            vals["name"] = str(name) + str(guardian.name)
            vals["mobile"] = guardian.mobile
            vals["email"] = guardian.email

            # name = vals.get("name") + '' + (vals.get("guardian_id.name") or "")        


        
        res = super(StudentStudent, self).create(vals)
        return res

    # def student_confirm(self):
    #     for rec in self:
    #         rec.confirm_date = fields.Date.today()
    #         rec.state = "active"


 
    def student_confirm(self):
        for rec in self:
            # manager_mail_template = self.env.ref('reg.email_confirm_school_reg_base')
            # rec.employee_confirm_id = self.env["hr.employee"].search( [("user_id", "=", self.env.uid)], limit=1 )
            rec.confirm_date = fields.Date.today()
            rec.state = "active"
            
            # contracts = self.env["student.student.contract"].sudo().browse(rec.partner_id.id)
            contracts = self.env["student.student.contract"].search( [("student_id", "=", self.id)])#, limit=1 )
            if contracts:
                for record in contracts:
                    record.write({"state": "active"}) 


 
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
            # rec.blocked_employee_id = self.env["hr.employee"].search( [("user_id", "=", self.env.uid)], limit=1)
            rec.userblocked_date = fields.Date.today()

    def reset_draft(self):
        for rec in self:
            rec.state = "draft"

    def student_in_active(self):
        for rec in self:
            rec.state = "in_active"
    
    def action_archive(self):
        for rec in self:
            rec.active = False

    # Add a field to store this student's unique sequence number
    student_seq = fields.Char(string="Student Sequence", readonly=True)
    student_number = fields.Char(string="Student Number", readonly=True)
 
    @api.constrains("display_name")
    def _check_name(self):
        partner_rec = self.env["student.student"].search(
            [("display_name", "=", self.display_name), ("id", "!=", self.id)]
        )
        if partner_rec:
            raise UserError(_("مكرر! الاسم موجود من قبل ."))

    @api.constrains("id_number")
    def _check_id_number(self):
        partner_rec = self.env["student.student"].search(
            [("id_number", "=", self.id_number), ("id", "!=", self.id)]
        )
        if partner_rec:
            raise UserError(_("مكرر! هذه الهوية موجودة من قبل   "))


    # add analtic account of related fields 

    analytic_accounts = fields.Many2many("account.analytic.account", string="Analytic Accounts")
    @api.model
    def create(self, vals):
        vals["analytic_accounts"] = self._get_analytic_accounts(vals)
        return super(StudentStudent, self).create(vals)

    def write(self, vals):
        vals["analytic_accounts"] = self._get_analytic_accounts(vals)
        return super(StudentStudent, self).write(vals)
    
    @api.model
    def create(self, vals):
        vals["analytic_accounts"] = self._get_analytic_accounts(vals)
        return super(StudentStudent, self).create(vals)
    
    def write(self, vals):
        vals["analytic_accounts"] = self._get_analytic_accounts(vals)
        return super(StudentStudent, self).write(vals)
    
    def _get_analytic_accounts(self, vals):
        analytic_accounts = []
        if vals.get("class_id"):
            class_rec = self.env["classes"].browse(vals["class_id"])
            if class_rec.analytic_account_id:
                analytic_accounts.append(class_rec.analytic_account_id.id)
        if vals.get("stage_id"):
            stage_rec = self.env["stages"].browse(vals["stage_id"])
            if stage_rec.analytic_account_id:
                analytic_accounts.append(stage_rec.analytic_account_id.id)
        if vals.get("track_id"):
            track_rec = self.env["tracks"].browse(vals["track_id"])
            if track_rec.analytic_account_id:
                analytic_accounts.append(track_rec.analytic_account_id.id)
        if vals.get("partner_id"):
            partner_rec = self.env["res.partner"].browse(vals["partner_id"])
            # if partner_rec.analytic_account_id:
            #     analytic_accounts.append(partner_rec.analytic_account_id.id)
        return [(6, 0, analytic_accounts)]


 
    # def _get_analytic_accounts(self, vals):
    #     analytic_accounts = []
    #     if vals.get("class_id"):
    #         stage_rec = stage_id = self.class_id.stage_id
    #         track_rec = track_id = self.class_id.stage_id.track_id
    #         class_rec = self.env["classes"].browse(vals["class_id"])
    #         if class_rec.analytic_account_id:
    #             analytic_accounts.append(class_rec.analytic_account_id.id)
    #             analytic_accounts.append(stage_rec.analytic_account_id.id)
    #             analytic_accounts.append(track_rec.analytic_account_id.id)
     
    #     # if vals.get("stage_id"):
    #     #     # stage_rec = self.env["stages"].browse(vals["stage_id"])
    #     #     # if stage_rec.analytic_account_id:
    #     # if vals.get("track_id"):
    #     #     # track_rec = self.env["tracks"].browse(vals["track_id"])
    #     #     # if track_rec.analytic_account_id:
    #     if vals.get("partner_id"):
    #         partner_rec = self.env["res.partner"].browse(vals["partner_id"])
    #         if partner_rec.analytic_account_id:
    #             analytic_accounts.append(partner_rec.analytic_account_id.id)
    #     return [(6, 0, analytic_accounts)]


class DropoffReason(models.Model):
    _name = "student.student.dropoff"
    _description ="..."

    student_id = fields.Many2one("student.student")
    guardian_id = fields.Many2one("student.guardian")
    reason = fields.Many2one("dropoff.reasons", string="Reason")

    def action_lost_reason_apply(self):
        active_ids = self.env.context.get('active_ids')
        students = self.env['student.student'].browse(active_ids)
        reason_id = self.reason.id  # Access the ID of the selected reason
        reason = self.env['dropoff.reasons'].browse(reason_id)
        reason_id = reason.id  # Access the ID of the selected reason
        students.write({'reason': reason_id})
        return {'type': 'ir.actions.act_window_close'}
