# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
# from odoo.exceptions import Warning, UserError
from odoo.exceptions import UserError

class Studentguardian(models.Model):
    
    _name = 'student.guardian'
    _description = 'Student guardian '
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']      # odoo11
    _order = 'id desc'
    
    # def unlink(self):
    #     for rec in self:
    #         if rec.state not in ('draft', 'in_active', 'blocked'):
    #             raise UserError(_('You can not delete Student guardian which is not in draft or cancelled or blocked state.'))
    #     return super(Studentguardian, self).unlink()
    
    sub_guardian_ids = fields.One2many('student.guardian','sub_guardian_id',string='Sub Guardians')
    sub_guardian_id = fields.Many2one('student.guardian',string='Sub Guardian')
    number = fields.Char(string='Family Number',  index=True, readonly=True, tracking=True )
    name = fields.Char(string="Family Name", index=True, tracking=True )
    state = fields.Selection([
        ('draft', 'New'),
        ('active', 'Active'),
        ('blocked', 'Blocked'),
        ('in_active', 'In Active'),
        ],
        default='draft',
        srting="Family State",
        tracking=True
    )


    
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

    active = fields.Boolean(default=True)
    gender = fields.Many2one('gender', required=True, copy=True, tracking=True)
    nationality = fields.Many2one('res.country', required=True, copy=True, tracking=True)
    id_type = fields.Many2one('id.type', required=True, copy=True, tracking=True)
    id_number = fields.Char('ID Number', required=True, copy=True, tracking=True)
    active =fields.Boolean(default=True)
    gender = fields.Many2one('gender', required=True, copy=True,  tracking=True,)
    nationality = fields.Many2one('res.country', required=True, copy=True,  tracking=True,)
    id_type = fields.Many2one('id.type', required=True, copy=True,  tracking=True,)
    id_number = fields.Char('Id Number', required=True, copy=True,  tracking=True,)
    tage = fields.Many2many('res.partner.category', 'guardian_id', index=True, required=True, copy=True,  tracking=True,)
    know_us = fields.Many2one('know.us', required=True, copy=True,  tracking=True,)
    work_type = fields.Many2one('work.type', required=True, copy=True,  tracking=True,)
    work_type_name = fields.Char(related='work_type.name')
    work_source = fields.Char('Work Source', required=True, copy=True,  tracking=True,)
    partner_id = fields.Many2one('res.partner', readonly=True, copy=True,  tracking=True,)
    mobile = fields.Char('Mobile', required=True, copy=True, tracking=True,)
    mobile2 = fields.Char('Mobile2', required=True, copy=True,  tracking=True,)
    job_position = fields.Char('Job Position',  required=True, copy=True, tracking=True,)
    email = fields.Char('Email',  required=True,  copy=True,  tracking=True,)
    student_ids = fields.One2many('student.student','guardian_id',string='Students')
    sub_guardian_id = fields.Many2one('student.guardian',string='Sub Guardian')
    guardian_date = fields.Date(string='Guardian Date', default=fields.Date.today(), required=True, copy=True, tracking=True, )
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.user.company_id, required=True, copy=True, )
    date_end = fields.Date( string='guardian Deadline', readonly=True, help='Last date for the guardian to be needed', copy=True,)
    date_done = fields.Date( string='Date Done', readonly=True,  help='Date of Completion of guardian Student', )      
    confirm_date = fields.Date( string='Confirmed Date', readonly=True,copy=False,)
    userblocked_date = fields.Date(  string='Blocked Date',  readonly=True, copy=False, )
    employee_confirm_id = fields.Many2one('hr.employee', string='Confirmed by',  readonly=True,copy=False, )
    blocked_employee_id = fields.Many2one('hr.employee', string='Blocked by',  readonly=True,copy=False, )
    relative_relation = fields.Many2one('relative.relation',string='Relative Relation')
    proof_of_kinship = fields.Binary(string='Proof of Kinship')
    is_family = fields.Boolean('IS Familly')
    is_main = fields.Boolean('IS Main Guardian ')

    sale_orders = fields.Many2many(
        comodel_name='sale.order',
        compute='_compute_sale_orders',
        string='Sale Orders',
        readonly=True
    )    
    qutetions_ids  = fields.Many2many(
        comodel_name='sale.order',
        compute='_compute_sale_orders',
        string='Sale Orders',
        readonly=True
    )


    def _compute_sale_orders(self):
        for guardian in self:
            students = guardian.student_ids
            sale_orders = self.env['sale.order'].search([
                ('partner_id', 'in', guardian.student_ids.mapped('partner_id').ids), ('state', '=', 'sale')
            ])
            sale_qutetions = self.env['sale.order'].search([
                ('partner_id', 'in', guardian.student_ids.mapped('partner_id').ids), ('state', '!=', 'sale')
            ])
            guardian.sale_orders = sale_orders
            guardian.qutetions_ids = sale_qutetions 
    
    order_count = fields.Integer(string='Order Count', compute='_compute_order_count')

    @api.depends('sale_orders')
    def _compute_order_count(self):
        for guardian in self:
            guardian.order_count = len(guardian.sale_orders)


    def action_gurdian_order_count(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Order Count',
            'res_model': 'sale.order',
            'domain': [('partner_id', 'in', self.student_ids.mapped('partner_id').ids)],
            'view_mode':'tree,form',
            'target': 'current',
    
        }
# - ----------------------------------------------------------------------------------               
    invoices = fields.Many2many(
        comodel_name='account.move',
        compute='_compute_invoices',
        string='Invoices',
        readonly=True
    )

    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    total_remaining_amount = fields.Float(string='Total Remiine Amount', compute='_compute_invoices')
    @api.depends('invoices')
    def _compute_invoice_count(self):
        for guardian in self:
            guardian.invoice_count = len(guardian.invoices)


    def action_gurdian_invoice_count(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Invoices Count',
            'res_model': 'account.move',
            'domain': [('partner_id', 'in', self.student_ids.mapped('partner_id').ids),('move_type', '=', 'out_invoice')],
            'view_mode':'tree,form',
            'target': 'current',
    
        }

    def _compute_invoices(self):
        for guardian in self:
            students = guardian.student_ids

            invoices = self.env['account.move'].search([
                        ('partner_id', 'in', guardian.student_ids.mapped('partner_id').ids),
                        ('move_type', '=', 'out_invoice')  # Optional: Filter for sales invoices only
                    ])
            if invoices:
                guardian.invoices = invoices
                guardian.total_remaining_amount = sum(invoice.amount_residual for invoice in invoices)
            else:
                guardian.invoices = False
                guardian.total_remaining_amount = 0
   
    student_count = fields.Integer(string='Student Count', compute='_compute_student_count')
    
    @api.depends('student_ids')
    def _compute_student_count(self):
        for guardian in self:
            guardian.student_count = len(guardian.student_ids)

    def action_gurdian_students(self):
        return{
            'type': 'ir.actions.act_window',
            'name': 'Students',
            'res_model': 'student.student',
            'domain': [('guardian_id','=',self.id)],
            'view_mode':'tree,form',
            'target': 'current',
    
        }
        
    # student_ids is a One2many or Many2many field that references students related to the guardian
    # Add the rest of your fields and methods here

    
    # seq 
    @api.model
    def create(self, vals):
        if vals.get('number', _('New')) == _('New'):
            vals['number'] = self.env['ir.sequence'].next_by_code('student.guardian.seq') or _('New')
######################### guardian_id = vals.get("guardian_id")###############
        partner_vals = {
            # "guardian_id": vals.get("id"),
            "name": vals.get("name"),
            "mobile": vals.get("mobile"),
            "email": vals.get("email"),
        }


        # Create the partner with the provided values
        partner = self.env["res.partner"].create(partner_vals)
        partner.write({"guardian_id": self.id})
        # Set the partner on the student
        vals["partner_id"] = partner.id
  ########################################################################      
        res = super(Studentguardian, self).create(vals)
        return res
    
    def family_confirm(self):
        for rec in self:
            # manager_mail_template = self.env.ref('reg.email_confirm_school_reg_base')
            # rec.employee_confirm_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.confirm_date = fields.Date.today()
            rec.state = 'active'
            # if manager_mail_template:
            #     manager_mail_template.send_mail(self.id)
            
    def family_blocked(self):
        for rec in self:
            rec.state = 'blocked'
            # rec.blocked_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.userblocked_date = fields.Date.today()
    
    def family_in_active(self):
        for rec in self:
            rec.state = 'in_active'

    def reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_archive(self):
        for rec in self:
            rec.active= False

    # @api.model
    # def create(self, vals):
    #     # guardian_id = vals.get("guardian_id")
    #     partner_vals = {
    #         # "guardian_id": vals.get("id"),
    #         "name": vals.get("name"),
    #         "mobile": vals.get("mobile"),
    #         "email": vals.get("email"),
    #     }


    #     # Create the partner with the provided values
    #     partner = self.env["res.partner"].create(partner_vals)
    #     partner.write({"guardian_id": self.id})
    #     # Set the partner on the student
    #     vals["partner_id"] = partner.id


    #     guardian = super(Studentguardian, self).create(vals)
    #     return guardian
    # Add a field to store the last sequence number for this guardian's students
    last_student_seq = fields.Integer(string='Last Student Sequence', default=0)
