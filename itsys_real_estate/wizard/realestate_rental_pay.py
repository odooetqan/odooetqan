# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time
import datetime
from datetime import datetime, date,timedelta
from dateutil import relativedelta

class customer_rental_payment_check(models.TransientModel):
    _name = 'customer.rental.payment.check'
    
    contract= fields.Many2one('rental.contract','Rental Contract',required=True)
    partner= fields.Many2one('res.partner','Tenant',required=True)
    account= fields.Many2one('account.account','Account', )
    journal= fields.Many2one('account.journal','Journal', )
    loan_line= fields.One2many('loan.line.rs.rent.wizard', 'loan_id')
    payment_method= fields.Selection([('cash','Cash'),('cheque','Cheque')], 'Payment Method', required=True, default='cash')
    discount_cash_total= fields.Float('Discount (Amt.) ')
    discount_percent_total= fields.Float('Discount %')
    select_all= fields.Boolean('Select all') 
    apply_penalty= fields.Boolean('Apply penalty for late payments?')

    @api.onchange('select_all')    
    def onchange_select(self):
        if self.contract:
            loan_lines=[]
            for line in self.contract.loan_line:
                if not line.paid:
                    if self.select_all:
                        loan_lines.append((0,0,{'to_be_paid':True,
                                                'date':line.date,
                                                'amount':line.amount,
                                                'amount_untaxed': line.amount_untaxed,
                                                'tax': line.amount_tax,
                                                'rental_line_id': line.id,
                                                'name':line.name}))
                    else:
                        loan_lines.append((0,0,{'to_be_paid':False,
                                                'date':line.date,
                                                'amount':line.amount,
                                                'amount_untaxed': line.amount_untaxed,
                                                'tax': line.amount_tax,
                                                'rental_line_id': line.id,
                                                'name':line.name}))
            return {'value': {'loan_line':loan_lines}}

    @api.onchange('discount_cash_total')
    def onchange_discount_cash(self):
        if self.discount_cash_total>0:
            self.discount_percent_total= 0.0

    @api.onchange('discount_percent_total')
    def onchange_discount_percent(self):
        if self.discount_percent_total>0:
            self.discount_cash_total= 0.0

    @api.onchange('partner')
    def onchange_partner(self):
        if self.partner:
            contracts=[]
            contract_ids = self.env['rental.contract'].search([('partner_id', '=', self.partner.id)])
            for obj in contract_ids:
                contracts.append(obj.id)
            return {'domain': {'contract': [('id', 'in', contracts)]}}

    @api.onchange('contract')
    def onchange_contract(self):
        if self.contract:
            loan_lines=[]
            for line in self.contract.loan_line:
                if not line.paid:
                    loan_lines.append((0,0,{
                                            'date':line.date,
                                            'amount':line.amount,
                                            'rental_line_id': line.id,
                                            'name':line.name}))

            self.loan_line= loan_lines
            self.partner=self.contract.partner_id.id

    def create_voucher(self, rec, type, amt, date, name, line_id=False):
        voucher_obj = self.env['account.payment']
        payment_method= self.env.ref(
            'account.account_payment_method_manual_out')
        vals= {
            'rental_line_id': line_id,
            'real_estate_ref': rec.contract.name,
            'journal_id': rec.journal.id,
            'payment_type': type,
            'date': date,
            'amount': amt,
            'payment_method_id': payment_method.id,
            'partner_id': rec.contract.partner_id.id,
            'partner_type': 'customer',
            'ref': name,
        }
        voucher_id = voucher_obj.create(vals)
        return voucher_id

    def apply_discount(self, rec):
        lines_discount=0
        total_amount=0
        for line in rec.loan_line:
            if line.to_be_paid:
                lines_discount += (line.amount*line.discount_percent)/100.0+line.discount_cash
                total_amount+=line.amount
        total_discount = total_amount*rec.discount_percent_total/100.0 + rec.discount_cash_total
        total_discount += lines_discount

        if total_discount > 0:
            default_discount_account= self.env['res.config.settings'].browse(self.env['res.config.settings'].search([])[-1].id).discount_account.id if self.env['res.config.settings'].search([]) else ""
            if not default_discount_account:
                raise UserError(_('Please set default Discount Account!'))
            dt= fields.Date.context_today
            voucher = self.create_voucher(self, 'inbound', total_discount, dt, 'Allowed Discount')
            return voucher


    def pay(self):
        penalty_obj = self.env['late.payment.penalties']
        line_ids=[]
        vouchers = []
        today = fields.Date.context_today
        total_penalties = 0
        if self.payment_method=='cash':
            for line in self.loan_line:
                if line.to_be_paid:
                    total_penalties+=penalty_obj.get_penalties(line)
                    line_ids.append(line.rental_line_id.id)
            if line_ids:
                if not self.contract.partner_id.property_account_receivable_id.id:
                    raise UserError(_('Please set receivable account for Partner'))
                loan_line_rs_own_obj = self.env['loan.line.rs.rent'].browse(line_ids)
                for line in loan_line_rs_own_obj:
                    amt = line.amount
                    dt = line.date
                    name=str(' Regarding Rental Contract ')+str(self.contract.name)
                    v= self.create_voucher(self, 'inbound', amt, dt, name, line.id)
                    v.action_post()
                    vouchers.append(v.id)
                    line.paid=True
                discount_voucher= self.apply_discount(self)
                if discount_voucher:
                    vouchers.append(discount_voucher)
                if total_penalties>0:
                    penalty_str=str(' Penalty on Rental Contract ')+str(self.contract.name)
                    v= self.create_voucher(self, 'inbound', total_penalties, today, penalty_str)
                    v.action_post()
                    vouchers.append(v.id)

                return {
                    'name': _('Vouchers'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', vouchers)],
                    'res_model': 'account.payment',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                }

class loan_line_rs_rent_wizard(models.TransientModel):
    _name = 'loan.line.rs.rent.wizard'
    
    date= fields.Date('Date')
    name= fields.Char('Name')
    serial= fields.Char('#')
    empty_col= fields.Char(' ',readonly=1)
    amount= fields.Float('Payment', digits=(16, 4),)
    rental_line_id= fields.Many2one('loan.line.rs.rent')
    to_be_paid= fields.Boolean('Pay')        
    loan_id= fields.Many2one('customer.rental.payment.check', '',ondelete='cascade', readonly=True)
    discount_cash= fields.Float('Discount (Amt.) ')
    discount_percent= fields.Float('Discount %')

    def onchange_discount_cash(self, discount):
        if discount>0:
            return {'value': {'discount_percent':0.0}}

    def onchange_discount_percent(self, discount):
        if discount>0:
            return {'value': {'discount_cash':0.0}}