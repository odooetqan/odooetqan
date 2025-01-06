# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResStudentInherit(models.Model):
    _inherit = 'student.student'

    partner_id = fields.Many2one('res.partner',
                                  string='Partner ', ondelete='restrict', auto_join=True,
                                  help='Employee-related data of the user')

    # @api.multi
    def create_partner_from_student(self):
        """Creates a partner record associated with the current student."""
        for student in self:
            partner_vals = {
                'name': student.display_name,
                'student_id': student.id,
                'phone': student.mobile,
                'mobile': student.mobile,
                'email': student.email,
                # 'company_id': self.env.ref('base.main_company').id,
                # 'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
            }
            partner = self.env['res.partner'].create(partner_vals)
            student.partner_id = partner.id

        return True

# # -*- coding: utf-8 -*-
# from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError

# class ResStudentInherit(models.Model):
#     _inherit = 'student.student'

#     partner_id = fields.Many2one('res.partner',
#                                   string='Partner ',
#                                 #   , ondelete='restrict', auto_join=True,
#                                   help='Partner-related data of the Student')

#     @api.model
#     def create(self, vals):
#         """Creates a partner record when a new student is created."""
#         # Call the original create method to create the student
#         student = super(ResStudentInherit, self).create(vals)

#         # Create the partner record
#         partner_vals = {
#             'name': vals.get('display_name'),
#             'student_id': student.id,
#             'phone': vals.get('mobile'),
#             'mobile': vals.get('mobile'),
#             'email': vals.get('email'),
#         }
#         partner = self.env['res.partner'].create(partner_vals)

#         # Link the partner to the student
#         student.partner_id = partner

#         return student
    
    

# -*- coding: utf-8 -*-
# from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError

# class ResStudentInherit(models.Model):
#     _inherit = 'student.student'

#     partner_id = fields.Many2one('res.partner',
#                                   string='Partner '
#                                 #   , ondelete='restrict', auto_join=True,
#                                   help='Partner-related data of the Student')

#     # @api.model
#     def create_partner_students(self):
#         """This code is to create an partner while creating an user."""

#         result['partner_id'] = self.env['res.partner'].create({
#                                                                 'name': result['display_name'],
#                                                                 'student_id': result['id'],
#                                                                 'phone': result['mobile'],
#                                                                 'mobile': result['mobile'],
#                                                                 'email': result['email'],
#                                                                        })
        
#         raise UserError(_("Partner was ceated...!    "))

        

#         # return result
