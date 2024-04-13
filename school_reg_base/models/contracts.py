#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# , Warning
# class Students(models.Model):
#     _inherit = 'student.student'

class Partner(models.Model):
    # _name = "student.student"

    _name = "student.student.contract"


    name = fields.Char('الاسم')
    mobile = fields.Char('الموبايل')
    id_number = fields.Char('الهوية')
    student_id = fields.Many2one('student.student')
    partner_id = fields.Many2one('res.partner', related = "student_id.partner_id")#compute= '_compute_partner_id')
    # def _compute_partner_id(self):
    #     partner_id  = self.student_id.partner_id
    #     if partner_id:
    #         return partner_id
    #     else:
    #         return False
            
    building_no = fields.Char(string=" Building No ", help="Building No")
    district = fields.Char(string="District", help="District")
    code = fields.Char(string="Code", help="Code")
    additional_no = fields.Char(string="  Addtion", help="Additional No")
    other_id = fields.Char(string=" Other", help="Other ID") 
    id_number = fields.Char(string="Id number", default="10000000001")
    nationality = fields.Many2one('res.country',string='الجنسية')
    unit_number = fields.Char('رقم الوحدة ')
    building_number = fields.Char('رقم المبني')
    
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
