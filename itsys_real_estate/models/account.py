# -*- coding: utf-8 -*-
from odoo import api, fields, models

class account_voucher(models.Model):
    _inherit = "account.payment"

    reservation_id=  fields.Many2one('unit.reservation','Reservation')
    real_estate_ref= fields.Char('Real Estate Ref.')
    ownership_line_id= fields.Many2one('loan.line.rs.own','Ownership Installment')
    ownership2_line_id= fields.Many2one('loan.line.rs.own','Ownership Installment')
    rental_line_id= fields.Many2one('loan.line.rs.rent','Rental Contract Installment')

class account_move(models.Model):
    _inherit = "account.move"

    real_estate_ref = fields.Char('Real Estate Ref.')
    ownership_line_id = fields.Many2one('loan.line.rs.own', 'Ownership Installment')
    ownership2_line_id = fields.Many2one('loan.line.rs.own', 'Ownership Installment')
    rental_line_id = fields.Many2one('loan.line.rs.rent', 'Rental Contract Installment')
    property_owner_id = fields.Many2one('res.partner', string="Owner")

class account_move_line(models.Model):
    _inherit = "account.move.line"
    commissioned= fields.Boolean('Commissioned')