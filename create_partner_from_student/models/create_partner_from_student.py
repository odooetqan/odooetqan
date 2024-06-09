# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ResStudentInherit(models.Model):
    _inherit = 'student.student'

    partner_id = fields.Many2one('res.partner',
                                  string='Partner ', ondelete='restrict', auto_join=True,
                                  help='Employee-related data of the user')

    # @api.model
    def create_partner_students(self):
        """This code is to create an partner while creating an user."""

        result['partner_id'] = self.env['res.partner'].create({
                                                                'name': result['display_name'],
                                                                'student_id': result['id'],
                                                                'phone': result['mobile'],
                                                                'mobile': result['mobile'],
                                                                'email': result['email'],
                                                                       })
        
        raise UserError(_("Partner was ceated...!    "))

        

        # return result
