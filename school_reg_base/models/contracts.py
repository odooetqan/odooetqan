#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# , Warning
# class Students(models.Model):
#     _inherit = 'student.student'

class StudentStudentContract(models.Model):
    # _name = "student.student"
    _name = "student.student.contract"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']      # odoo11
    _order = 'id desc'
    
    name = fields.Char(related='partner_id.name')
    state = fields.Selection([("draft", "Draft"), ("active", "Active"),("confirm", "confirm"), ("blocked", "Blocked"), ("in_active", "In Active"),],default="draft",string="Student State",tracking=True,) 
    reference = fields.Char(string='Contract Refrence', required=True, readonly=True, default=lambda self: _('New'))
    mobile = fields.Char('الموبايل')
    id_number = fields.Char('الهوية')
    student_id = fields.Many2one('student.student')
    partner_id = fields.Many2one('res.partner', related = "student_id.partner_id")#compute= '_compute_partner_id')
    building_no = fields.Char(string=" Building No ", help="Building No")
    district = fields.Char(string="District", help="District")
    code = fields.Char(string="Code", help="Code")
    additional_no = fields.Char(string="  Addtion", help="Additional No")
    other_id = fields.Char(string=" Other", help="Other ID") 
    id_number = fields.Char(string="Id number", default="10000000001")
    nationality = fields.Many2one('res.country',string='الجنسية')
    unit_number = fields.Char('رقم الوحدة ')
    building_number = fields.Char('رقم المبني')
############################################################################################################################
    student_number = fields.Char(related="student_id.number", index=True, readonly=True, tracking=True)
    family_number = fields.Char(related="student_id.family_number", index=True, readonly=True, tracking=True)
    family_name = fields.Char(related="student_id.family_name", index=True, readonly=True, tracking=True)
    family_number = fields.Char(related="student_id.family_number", index=True, readonly=True, tracking=True)
    class_id = fields.Many2one("classes", related="student_id.class_id",string="Education Class", required=True, copy=True )
    stage_id = fields.Many2one("stages", related="student_id.stage_id", string="Stage", tracking=True, required=True, )
    section_id = fields.Many2one("sections", related="student_id.section_id", string="Section",  tracking=True, required=True, )
    track_id = fields.Many2one("tracks", related="student_id.track_id", string="Track", tracking=True,  required=True,)
    secondary_major = fields.Many2one("secondry.majors", related="student_id.secondary_major", string="Secondary Major", tracking=True)
    ex_school = fields.Many2one("ex.schools", related="student_id.ex_school", string="Ex School", required=True, copy=True)
    current_year = fields.Many2one("years", related="student_id.current_year", string="Current Year", copy=True)
    previous_year = fields.Many2one("years", related="student_id.previous_year", string="Previous Year", required=True, copy=True)
    gender = fields.Many2one("gender", related="student_id.gender", string="Gender", required=True, copy=True, tracking=True)
    nationality = fields.Many2one("res.country", related="student_id.nationality", string="Nationality", required=True, copy=True, tracking=True)
    id_type = fields.Many2one("id.type", related="student_id.id_type", string="ID Type", required=True, copy=True, tracking=True)
    id_number = fields.Char(string="ID Number", related="student_id.id_number", required=True, copy=True, tracking=True)
    # tage = fields.Many2many("res.partner.category", related="student_id.tage", "student_id",string="Tage", copy=True, tracking=True)
    birth_date = fields.Date(string="Birth Date", related="student_id.birth_date")
    hijri_date = fields.Date(string="Hijri Date", related="student_id.hijri_date")
    reason = fields.Many2one("dropoff.reasons", string="Reason", related="student_id.reason")
    sibling_discount = fields.Many2one("discount.type", string="Sibling Discount", related="student_id.sibling_discount")
    student_discount = fields.One2many("discounts","student_id", string="Student Discount", related="student_id.student_discount")    
    know_us = fields.Many2one("know.us",required=True,copy=True,tracking=True, related="student_id.know_us")
    partner_id = fields.Many2one("res.partner",required=False,copy=True,tracking=True, related="student_id.partner_id",    )
    mobile = fields.Char("Mobile",required=True,copy=True,tracking=True, related="student_id.mobile",    )
    mobile2 = fields.Char("Mobile2",required=True,copy=True,tracking=True, related="student_id.mobile2",    )
    email = fields.Char("Email",required=True,copy=True,tracking=True, related="student_id.email",    )
    guardian_id = fields.Many2one("student.guardian", string="Guardian", required=True, related="student_id.guardian_id")
    student_date = fields.Date(string="Student Date",default=fields.Date.today(),required=True,copy=True,tracking=True, related="student_id.student_date",    )
    company_id = fields.Many2one("res.company",string="Company",default=lambda self: self.env.user.company_id,required=True,copy=True, related="student_id.company_id",)
    sign = fields.Image(string='Sign', related='company_id.sign')
    seal = fields.Image(string='Seal', related='company_id.seal')
    date_end = fields.Date(string="Student Deadline",help="Last date for the student to be needed",copy=True, related="student_id.date_end",    )
    date_done = fields.Date(string="Date Done",help="Date of Completion of student Student", related="student_id.date_done",    )
    confirm_date = fields.Date(string="Confirmed Date",copy=False, related="student_id.confirm_date",    )
    userblocked_date = fields.Date(string="Blocked Date",readonly=True,copy=False, related="student_id.userblocked_date",    )
    employee_confirm_id = fields.Many2one("hr.employee",string="Confirmed by",readonly=True,copy=False, related="student_id.employee_confirm_id",    )
    blocked_employee_id = fields.Many2one("hr.employee",string="Blocked by",readonly=True,copy=False, related="student_id.blocked_employee_id",    )
    street = fields.Char( related="student_id.street")
    street2 = fields.Char( related="student_id.street2")
    city = fields.Char( related="student_id.city")
    is_secondary = fields.Boolean( related="student_id.is_secondary")
    country_id = fields.Many2one('res.country',related='partner_id.country_id')
############################################################################################################################

    education_path = fields.Selection(
        string='المسار',
        selection=[
            ('مسار وطني','مسار وطني'),
            ('مسار مصري','مسار مصري'),
            ('مسار دولي','مسار دولي'),
            ('مجموعات مسائية','مجموعات مسائية'),
        ],
    )

    education_class = fields.Selection(
        string='الصف الدراسي',
        selection=[
            ('حضانة','حضانة'),
            ('مستوى أول روضة','مستوى أول روضة'),
            ('مستوى ثاني روضة','مستوى ثانى حضانة'),
            ('مستوى ثالث روضة','مستوى ثالث حضانة'),
            ('الصف الأول الابتدائي','الابتدائي الصف الاول'),
            ('الصف الثاني الابتدائي','الابتدائي الصف الثاني'),
            ('الصف الثالث الابتدائي','الابتدائي الصف الثالث'),
            ('الصف الرابع الابتدائي','الابتدائي الصف الرابع'),
            ('الصف الخامس الابتدائي','الابتدائي الصف الخامس'),
            ('الصف السادس الابتدائي','الابتدائي الصف السادس'),
            ('abc','الابتدائي الصف السابع'),
            ('cde','الابتدائي الصف الثامن'),
            ('الصف الأول متوسط','الصف الأول متوسط'),
            ('الصف الثاني متوسط','الصف الثاني متوسط'),
            ('الصف الثالث متوسط','الصف الثالث متوسط'),
            ('الصف الأول ثانوي','الثانوية الصف الأول'),
            ('الصف الثاني ثانوي','الثانوية الصف الثاني'),
            ('الصف الثالث ثانوي','الثانوية الصف الثالث'),
        ],
    )
    
    education_level = fields.Selection(
        string='المرحلة الدراسية',
        selection=[
            ('مرحلة رياض الأطفال','مرحلة رياض الأطفال'),
            ('المرحلة الإبتدائية','المرحلة الايتدائية'),
            ('المرحلة المتوسطة','المرحلة المتوسطة'),
            ('المرحلة الثانوية','المرحلة الثانوية'),
        ],
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

    @api.constrains('name')
    def _check_name(self):
        partner_rec = self.env['student.student'].search(
            [('name', '=', self.name), ('id', '!=', self.id)]) 
        if partner_rec:
            raise UserError(_('مكرر  ! هذا العميل موجود من قبل في جهات الاتصال .'))
    @api.constrains('mobile')
    def _check_mobile(self):
        partner_rec = self.env['student.student'].search(
            [('mobile', '=', self.mobile), ('id', '!=', self.id)]) 
        if partner_rec:
            raise UserError(_('مكرر ! هذا الرقم موجود في احدي جهات الاتصال '))
    @api.constrains('id_number')
    def _check_mobile(self):
        partner_rec = self.env['student.student'].search(
            [('id_number', '=', self.id_number), ('id', '!=', self.id)]) 
        if partner_rec:
            raise UserError(_('مكرر ! هذا الهوية موجود في احدي جهات الاتصال '))

# On Tue, 26 Nov 2019 at 11:17, shalin wilson <shalinwilson1994@gmail.com> wrote:
    _sql_constraints = [('phone', 'unique(phone)', 'Error Message')]
    # is subject your many2one field
    # _sql_constraints = [
    #     ('name', 'unique (name)', 'The name already Exists!'),
    # ]
    def test(self):

        pass
        
    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'student.student.contract') or _('New')
        res = super(StudentStudentContract, self).create(vals)
        return res

    def student_blocked(self):
        for rec in self:
            rec.state = "blocked"
            # rec.blocked_employee_id = self.env["hr.employee"].search( [("user_id", "=", self.env.uid)], limit=1)
            # rec.userblocked_date = fields.Date.today()

    def reset_draft(self):
        for rec in self:
            rec.state = "draft"

    def student_in_active(self):
        for rec in self:
            rec.state = "in_active"
    
    def action_archive(self):
        for rec in self:
            rec.active = False

    def student_confirm(self):
        for rec in self:
            rec.state = "confirm"            
