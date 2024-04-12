#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# , Warning


class Partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    building_no = fields.Char(string=" Building No ", help="Building No")
    district = fields.Char(string="District", help="District")
    code = fields.Char(string="Code", help="Code")
    additional_no = fields.Char(string="  Addtion", help="Additional No")
    other_id = fields.Char(string=" Other", help="Other ID") 
    
    @api.constrains('name')
    def _check_name(self):
        partner_rec = self.env['res.partner'].search(
            [('name', '=', self.name), ('id', '!=', self.id)]) 
        if partner_rec:
            raise UserError(_('مكرر  ! هذا العميل موجود من قبل في جهات الاتصال .'))
    @api.constrains('mobile')
    def _check_mobile(self):
        partner_rec = self.env['res.partner'].search(
            [('mobile', '=', self.mobile), ('id', '!=', self.id)]) 
        if partner_rec:
            raise UserError(_('مكرر ! هذا الرقم موجود في احدي جهات الاتصال '))
    @api.constrains('id_number')
    def _check_mobile(self):
        partner_rec = self.env['res.partner'].search(
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
