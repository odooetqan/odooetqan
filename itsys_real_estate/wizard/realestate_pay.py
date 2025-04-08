# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _

class customer_payment_check(models.TransientModel):
    _name = 'customer.payment.check'

    contract= fields.Many2one('ownership.contract','Ownership Contract',required=True)
    partner= fields.Many2one('res.partner','Partner',required=True)
    account= fields.Many2one('account.account','Account')
    journal= fields.Many2one('account.journal','Journal',required=True)
    loan_line= fields.One2many('loan.line.rs.wizard', 'loan_id')
    payment_method= fields.Selection([('cash','Cash'),('cheque','Cheque')], 'Payment Method', required=True, default='cash')
    cheque_number= fields.Char('Reference')
    discount_cash_total= fields.Float('Discount (Amt.)')
    discount_percent_total= fields.Float('Discount %')
    select_all= fields.Boolean('Select all')

    @api.onchange('contract')
    def onchange_contract(self):
        self.loan_line=None
        if self.contract:
            loan_lines=[]
            for line in self.contract.loan_line:
                if line.total_remaining_amount:
                    loan_lines.append((0,0,{'date':line.date,'amount':line.total_remaining_amount,'installment_line_id': line.id, 'name':line.name}))
            self.partner=self.contract.partner_id.id
            self.loan_line=loan_lines

    @api.onchange('select_all')
    def onchange_select(self):
        self.loan_line=None
        if self.contract:
            loan_lines=[]
            for line in self.contract.loan_line:
                if line.total_remaining_amount:
                    if self.select_all:
                        loan_lines.append((0,0,{'to_be_paid':True, 'date':line.date,'amount':line.total_remaining_amount,'installment_line_id': line.id, 'name':line.name}))
                    else:
                        loan_lines.append((0,0,{'to_be_paid':False, 'date':line.date,'amount':line.total_remaining_amount,'installment_line_id': line.id, 'name':line.name}))
            self.loan_line= loan_lines

    @api.onchange('discount_cash_total')
    def onchange_discount_cash(self):
        if self.discount_cash_total>0:
            self.discount_percent_total = 0.0

    @api.onchange('discount_percent_total')
    def onchange_discount_percent(self):
        if self.discount_percent_total>0:
            self.discount_cash_total = 0.0

    @api.onchange('partner')
    def onchange_partner(self):
        if self.partner:
            contracts=[]
            contract_ids = self.env['ownership.contract'].search([('partner_id', '=', self.partner.id),('state','=','confirmed')])
            for contract in contract_ids:
                contracts.append(contract.id)
            return {'domain': {'contract': [('id', 'in', contracts)]}}

    def create_voucher(self, rec, type, amt, date, name, partner_type, line_id=False, ):
        voucher_obj = self.env['account.payment']
        if partner_type=='customer':  payment_method= self.env.ref('account.account_payment_method_manual_out')
        else: payment_method= self.env.ref('account.account_payment_method_manual_in')
        vals= {
            'ownership_line_id': line_id,
            'real_estate_ref': rec.contract.name,
            'journal_id': rec.journal.id,
            'payment_type': type,
            'date': date,
            'amount': amt,
            'payment_method_id': payment_method.id,
            'partner_id': rec.contract.partner_id.id,
            'partner_type': partner_type,
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
            # default_discount_account= self.env['res.config.settings'].browse(self.env['res.config.settings'].search([])[-1].id).discount_account.id if self.env['res.config.settings'].search([]) else ""
            # if not default_discount_account:
            #     raise UserError(_('Please set default Discount Account!'))
            dt= fields.Date.today()
            voucher = self.create_voucher(self, 'outbound', total_discount, dt, 'Allowed Discount','supplier')
            return voucher

    def pay(self):
        penalty_obj = self.env['late.payment.penalties']
        vouchers = []
        today = str(fields.Date.context_today)
        total_penalties = 0
        if self.payment_method=='cash':
            for line in self.loan_line:
                if line.to_be_paid:
                    total_penalties+=penalty_obj.get_penalties(line)
                    installment_line_id= line.installment_line_id
                    if installment_line_id:
                        if not self.contract.partner_id.property_account_receivable_id.id:
                            raise UserError(_('Please set receivable account for Partner'))
                        loan_line_rs_own_obj = self.env['loan.line.rs.own'].browse(installment_line_id)
                        for line1 in loan_line_rs_own_obj:
                            amt = line.amount
                            dt = line1.date
                            name=str(' Regarding Ownership Contract ')+str(self.contract.name)
                            v= self.create_voucher(self, 'inbound', amt, dt, name, 'customer', line1.id)
                            vouchers.append(v.id)
                            v.action_post()
                            line1.total_paid_amount= line1.total_paid_amount+line.amount
                            self.contract.get_commission_paid(line.amount, line.date)

                        discount_voucher= self.apply_discount(self)
                        if discount_voucher:
                            vouchers.append(discount_voucher.id)
                        if total_penalties>0:
                            penalty_str=str(' Penalty on Ownership Contract ')+str(self.contract.name)
                            v= self.create_voucher(self, 'inbound', total_penalties, today, penalty_str, 'customer')
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

class loan_line_rs_wizard(models.TransientModel):
    _name = 'loan.line.rs.wizard'

    date= fields.Date('Date')
    name= fields.Char('Name')
    serial= fields.Char('#')
    empty_col= fields.Char(' ',readonly=True)
    amount= fields.Float('Payment', digits=(16, 4),)
    installment_line_id= fields.Integer('id ')
    to_be_paid= fields.Boolean('Pay')
    loan_id= fields.Many2one('customer.payment.check', '',ondelete='cascade', readonly=True)
    discount_cash= fields.Float('Discount (Amt.) ')
    discount_percent= fields.Float('Discount %')

    def onchange_discount_cash(self, discount):
        if discount>0:
            return {'value': {'discount_percent':0.0}}

    def onchange_discount_percent(self, discount):
        if discount>0:
            return {'value': {'discount_cash':0.0}}

