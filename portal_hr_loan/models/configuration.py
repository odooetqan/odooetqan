# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class GenderBase(models.Model):
    _name = "gender"
    _description = "Descripe gender of students and guadrians "

    name = fields.Char("Gender", tracking=True, required=True)


class IdType(models.Model):
    _name = "id.type"
    _description = "Descripe Identification type "

    name = fields.Char("ID Type", tracking=True, required=True)


class WorkType(models.Model):
    _name = "work.type"
    _description = "Descripe work type "

    name = fields.Char("Work Type", tracking=True, required=True)


class KnowUs(models.Model):
    _name = "know.us"
    _description = "Descripe how you are know about us "

    name = fields.Char("Know Us", tracking=True, required=True)
    
class RelativeRelation(models.Model):
    _name = "relative.relation"
    _description = "Descripe whats is  relative relation "

    name = fields.Char(string='Relative Relation', tracking=True, required=True)


class StudentStatus(models.Model):
    _name = "student.status"
    _description = "Descripe status of student"

    name = fields.Char("Student Status", tracking=True, required=True)
    need_reason = fields.Boolean("Need Reason")


class DiscouontType(models.Model):
    _name = "discount.type"
    _description = "Discount types"

    name = fields.Char("Discount Type", tracking=True)


class Discounts(models.Model):
    _name = "discounts"
    _description = "Discounts "

    name = fields.Char("Name", tracking=True, required=True)
    ratio = fields.Char("Ratio", tracking=True, required=True)

    discount_id = fields.Many2one("discount.type", tracking=True, required=True)
    discription = fields.Char("Discription", tracking=True, required=True)
    company_id = fields.Many2one("res.company", string="Company", default=1)


class SchoolssBase(models.Model):
    _name = "schools"
    _description = "Descripe gender of students and guadrians "

    name = fields.Char("Schools", tracking=True, required=True)


class dropofooReasonssBase(models.Model):
    _name = "dropoff.reasons"
    _description = "Descripe gender of students and guadrians "

    name = fields.Char("schools", tracking=True, required=True)


class StudentsBase(models.Model):
    _name = "students"
    _description = "Descripe students  "

    name = fields.Char("students", tracking=True, required=True)


class GuardianBase(models.Model):
    _name = "guardians"
    _description = "Descripe guadrians of students   "

    name = fields.Char("guardians", tracking=True, required=True)


class TracksBase(models.Model):
    _name = "tracks"
    _description = "Descripe Tracks of students "

    name = fields.Char("Tracks", tracking=True, required=True)


class SectionsBase(models.Model):
    _name = "sections"
    _description = "Descripe Sections of students  "

    name = fields.Char("Sections", tracking=True, required=True)
    track_id = fields.Many2one("tracks", tracking=True, required=True)


class StagesBase(models.Model):
    _name = "stages"
    _description = "Descripe Stages of students  "

    name = fields.Char("Stages", tracking=True, required=True)
    is_secondary = fields.Boolean("Stages", tracking=True)
    section_id = fields.Many2one("sections", tracking=True, required=True)
    track_id = fields.Many2one(
        "tracks", related="section_id.track_id", tracking=True, required=True
    )


class ClassesBase(models.Model):
    _name = "classes"
    _description = "Descripe Stages of students  "

    name = fields.Char("Class", tracking=True, required=True)
    stage_id = fields.Many2one("stages", string="stage", tracking=True, required=True)
    section_id = fields.Many2one("sections",related="stage_id.section_id" , tracking=True, required=True)
    track_id = fields.Many2one("tracks", tracking=True, related="stage_id.track_id" ,required=True)
    seq = fields.Integer(string="Class Sequences")

class SecondryMajorsBase(models.Model):
    _name = "secondry.majors"
    _description = "Descripe Stages of students  "

    name = fields.Char("Secondary Majors", tracking=True, required=True)
    stage_id = fields.Many2one("stages", tracking=True, required=True)
    section_id = fields.Many2one("sections",related="stage_id.section_id" , tracking=True, required=True)
    track_id = fields.Many2one("tracks", tracking=True, related="stage_id.track_id" ,required=True)


class ExSchools(models.Model):

    _name = "ex.schools"
    _description = "Descripe Stages of students  "

    name = fields.Char("ExSchools Name", tracking=True, required=True)
    outside_madinah = fields.Boolean("Outside Madinah", tracking=True, required=True)


class Years(models.Model):

    _name = "years"
    _description = "Descripe Years of students  "

    name = fields.Integer("Name", tracking=True, required=True)


class Fees(models.Model):

    _name = "fees"
    _description = "Descripe Fees of students  "

    name = fields.Char("Name", tracking=True, required=True)
    stage_id = fields.Many2one("stages", tracking=True, required=True)
    product_id = fields.Many2one("product.product", tracking=True, required=True)


class ProductsStudents(models.Model):

    _inherit = "product.product"
    _description = "Descripe Products of students  "

    fees_id = fields.One2many('fees','product_id', string='Student Fees')
    fees = fields.Boolean('Fees')
