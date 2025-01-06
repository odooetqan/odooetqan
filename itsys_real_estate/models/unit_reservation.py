# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models
import datetime
from odoo.tools.translate import _
import calendar
from odoo.exceptions import UserError, AccessError
from datetime import time, datetime, date,timedelta

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'

#     default_start_date = fields.Date('Default Start Date')

class unit_reservation(models.Model):
    _name = "unit.reservation"
    _description = "Property Reservation"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _contract_count_own(self):
        own_obj = self.env['ownership.contract']
        own_ids = own_obj.search([('reservation_id', '=', self.id)])
        self.contract_count_own = len(own_ids)

    def _contract_count_own2(self):
        own_obj = self.env['ownership2.contract']
        own_ids = own_obj.search([('reservation_id', '=', self.id)])
        self.contract_count_own = len(own_ids)

    def _contract_count_rent(self):
        rent_obj = self.env['rental.contract']
        rent_ids = rent_obj.search([('reservation_id', '=', self.id)])
        self.contract_count_rent = len(rent_ids)

    def _deposit_count(self):
        payment_obj = self.env['account.payment']
        payment_ids = payment_obj.search([('reservation_id', '=', self.id)])
        self.deposit_count = len(payment_ids)

    account_income= fields.Many2one('account.account','Income Account')
    account_analytic_id= fields.Many2one('account.analytic.account','Analytic Account')
    contract_count_own= fields.Integer(compute='_contract_count_own', string='Sales')
    contract_count_own2= fields.Integer(compute='_contract_count_own2', string='Sales')
    contract_count_rent= fields.Integer(compute='_contract_count_rent', string='Rentals')
    deposit_count= fields.Integer(compute='_deposit_count', string='Deposits')
    #Reservation Info
    name= fields.Char    ('Name', size=64, readonly=True)
    date= fields.Datetime    ('Reservation Date', default=fields.Datetime.now())
    date_payment= fields.Date    ('First Payment Date')
    #Building Info
    building= fields.Many2one('building','Building',)
    building_code= fields.Char    ('Code', size=16)
    #Building Unit Info
    building_unit= fields.Many2one('product.template','Building Unit',domain=[('is_property', '=', True),('state', '=', 'free')],required=True)
    unit_code= fields.Char    ('Code', size=16)
    floor= fields.Char    ('Floor', size=16)
    address= fields.Char    ('Address')
    pricing= fields.Integer   ('ٍPricing',)
    template_id= fields.Many2one('installment.template','Payment Template',)
    contract_id_own= fields.Many2one('ownership.contract','Ownership Contract',)
    contract_id_own2= fields.Many2one('ownership2.contract','Ownership Contract',)
    contract_id_rent= fields.Many2one('rental.contract','Rental Contract',)
    type= fields.Many2one('building.type','Building Unit Type',)
    status= fields.Many2one('building.status','Building Unit Status',)
    region= fields.Many2one('regions','Region',)
    user_id= fields.Many2one('res.users','Responsible', default=lambda self: self.env.user,)
    partner_id= fields.Many2one('res.partner','Customer')
    building_area= fields.Integer ('Building Unit Area m²',)
    loan_line= fields.One2many('loan.line.rs', 'loan_id')
    state= fields.Selection([('draft','Draft'),
                             ('confirmed','Confirmed'),
                             ('contracted','Contracted'),
                             ('canceled','Canceled')
                             ], 'State', default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    deposit= fields.Float('Deposit', digits=(16, 2),)

    def unlink(self):
        if self.state !='draft':
            raise UserError(_('You can not delete a reservation not in draft state'))
        super(unit_reservation, self).unlink()
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Reservation Number record must be unique !')
    ]

    def auto_cancel_reservation(self):
        try:
            reservation_pool = self.env['unit.reservation']
            reservation_hours = int(self.env['ir.config_parameter'].sudo().get_param('itsys_real_estate.reservation_hours'))
            timeout_reservation_ids=reservation_pool.search([('state','=','confirmed'),('date','<=',str(datetime.now() - timedelta(hours=reservation_hours)))])
            for reservation in timeout_reservation_ids:
                reservation.write({'state': 'canceled'})
                unit = reservation.building_unit
                unit.write({'state': 'free'})
        except:
            return "internal error"

    @api.onchange('building_unit')
    def onchange_unit(self):
        self.unit_code=self.building_unit.code
        self.floor=self.building_unit.floor
        self.type=self.building_unit.ptype
        self.address=self.building_unit.address
        self.status=self.building_unit.status
        self.building_area=self.building_unit.building_area
        self.building = self.building_unit.building_id.id
        self.region = self.building_unit.region_id.id

    def action_draft(self):
        self.write({'state':'draft'})

    def action_cancel(self):
        self.write({'state':'canceled'})
        unit = self.building_unit
        unit.write({'state':  'free'})

    def unit_status(self):
        return self.building_unit.state

    def action_confirm(self):
        self.write({'state':'confirmed'})
        unit = self.building_unit
        unit.write({'state': 'reserved'})

    def action_receive_deposit(self):
        if not self.deposit:
            raise UserError(_('Please set the deposit amount!'))
        return {
            'name': _('Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'view_id': self.env.ref('account.view_account_payment_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_payment_type': 'inbound',
                'default_partner_type':'customer',
                'default_amount':self.deposit,
                'default_partner_id':self.partner_id.id,
                'default_reservation_id': self.id,
            },
            'target': 'current'
        }

    def view_deposits(self):
        payment_obj = self.env['account.payment']
        payment_ids = payment_obj.search([('reservation_id', '=', self.id)])

        return {
            'name': _('Payments'),
            'domain': [('id', 'in', payment_ids.ids)],
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'account.payment',
            'type':'ir.actions.act_window',
            'nodestroy':True,
            'view_id': False,
            'target':'current',
        }

    def action_contract_ownership(self):
        return {
            'name': _('Ownership Contract'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ownership.contract',
            'view_id': self.env.ref('itsys_real_estate.ownership_contract_form_view').id,
            'type': 'ir.actions.act_window',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_building': self.building.id,
                'default_region': self.region.id,
                'default_building_code': self.building_code,
                'default_partner_id': self.partner_id.id,
                'default_building_unit': self.building_unit.id,
                'default_unit_code': self.unit_code,
                'default_floor': self.floor,
                'default_type': self.type.id,
                'default_status': self.status.id,
                'default_building_area': self.building_area,
                'default_reservation_id': self.id,
            },
            'target': 'current'
        }

    def action_contract_ownership2(self):
        return {
            'name': _('Ownership2 Contract'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ownership2.contract',
            'view_id': self.env.ref('itsys_real_estate.ownership2_contract_form_view').id,
            'type': 'ir.actions.act_window',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_building': self.building.id,
                'default_region': self.region.id,
                'default_building_code': self.building_code,
                'default_partner_id': self.partner_id.id,
                'default_building_unit': self.building_unit.id,
                'default_unit_code': self.unit_code,
                'default_floor': self.floor,
                'default_type': self.type.id,
                'default_status': self.status.id,
                'default_building_area': self.building_area,
                'default_reservation_id': self.id,
            },
            'target': 'current'
        }

    def action_contract_rental(self):
        return {
            'name': _('Rental Contract'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rental.contract',
            'view_id': self.env.ref('itsys_real_estate.rental_contract_form_view').id,
            'type': 'ir.actions.act_window',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_building': self.building.id,
                'default_region': self.region.id,
                'default_building_code': self.building_code,
                'default_partner_id': self.partner_id.id,
                'default_building_unit': self.building_unit.id,
                'default_unit_code': self.unit_code,
                'default_floor': self.floor,
                'default_type': self.type.id,
                'default_status': self.status.id,
                'default_building_area': self.building_area,
                'default_reservation_id': self.id,
            },
            'target': 'current'
        }


    def view_contract_own(self):
        own_obj = self.env['ownership.contract']
        own_ids = own_obj.search([('reservation_id', '=', self.id)])

        return {
            'name': _('Ownership Contract'),
            'domain': [('id', 'in', own_ids.ids)],
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'ownership.contract',
            'type':'ir.actions.act_window',
            'nodestroy':True,
            'view_id': False,
            'target':'current',
        }

    def view_contract_own2(self):
        own_obj = self.env['ownership2.contract']
        own_ids = own_obj.search([('reservation_id', '=', self.id)])

        return {
            'name': _('Ownership2 Contract'),
            'domain': [('id', 'in', own_ids.ids)],
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'ownership2.contract',
            'type':'ir.actions.act_window',
            'nodestroy':True,
            'view_id': False,
            'target':'current',
        }

    def view_contract_rent(self):
        rent_obj = self.env['rental.contract']
        rent_ids = rent_obj.search([('reservation_id', '=', self.id)])

        return {
            'name': _('Rental Contract'),
            'domain': [('id', 'in', rent_ids.ids)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'rental.contract',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'view_id': False,
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('unit.reservation')
        new_id = super(unit_reservation, self).create(vals)
        return new_id

    def add_months(self,sourcedate,months):
        month = sourcedate.month - 1 + months
        year = int(sourcedate.year + month / 12 )
        month = month % 12 + 1
        day = min(sourcedate.day,calendar.monthrange(year,month)[1])
        return date(year,month,day)

    def _prepare_lines(self,first_date):
        loan_lines=[]
        if self.template_id:
            pricing = self.pricing
            mon = self.template_id.duration_month
            yr = self.template_id.duration_year
            repetition = self.template_id.repetition_rate
            advance_percent = self.template_id.adv_payment_rate
            deduct = self.template_id.deduct
            if not first_date:
                raise UserError(_('Please select first payment date!'))
            adv_payment=pricing*float(advance_percent)/100
            if mon>12:
                x = mon/12
                mon=(x*12)+mon%12
            mons=mon+(yr*12)
            if adv_payment:
                loan_lines.append((0,0,{'amount':adv_payment,'date': first_date, 'name':_('Advance Payment')}))
                if deduct:
                    pricing-=adv_payment
            loan_amount=(pricing/float(mons))*repetition
            m=0
            i=2
            while m<mons:
                loan_lines.append((0,0,{'amount':loan_amount,'date': first_date,'name':_('Loan Installment')}))
                i+=1
                first_date = self.add_months(first_date, repetition)
                m+=repetition
        return loan_lines

class loan_line_rs(models.Model):
    _name = 'loan.line.rs'
    _order = 'serial'

    date= fields.Date('Date')
    name= fields.Char('Name')
    serial= fields.Integer('#')
    empty_col= fields.Char(' ', readonly=True)
    amount= fields.Float('Payment', digits=(16, 4),)
    paid= fields.Boolean('Paid')
    contract_partner_id= fields.Many2one(related='loan_id.partner_id', string="Partner")
    contract_building= fields.Many2one(related='loan_id.building', string="Building")
    contract_building_unit= fields.Many2one(related='loan_id.building_unit', string="Building Unit")
    loan_id= fields.Many2one('unit.reservation', '', readonly=True) #ondelete='cascade',
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
