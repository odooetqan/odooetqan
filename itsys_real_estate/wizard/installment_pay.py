# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _

class installment_payment_check(models.TransientModel):
    _name = 'installment.payment.check'

    payment_date = fields.Date(string="Payment Date", required=True,
        default=fields.Date.context_today)
    communication = fields.Char(string="Memo")
    amount = fields.Monetary('Amount')
    journal= fields.Many2one('account.journal','Journal',required=True)

    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

    discount_cash_total= fields.Float('Discount (Amt.)')
    discount_percent_total= fields.Float('Discount %')

    @api.model
    def default_get(self, fields):
        result = super(installment_payment_check, self).default_get(fields)
        model = self.env.context.get('active_model')
        remaining_amt=0
        if model == 'loan.line.rs.own':
            installment_id = self.env.context.get('active_id')
            installment = self.env['loan.line.rs.own'].sudo().browse(installment_id)
            remaining_amt= installment.total_remaining_amount
            result['amount'] = remaining_amt
            result['communication']= (installment.loan_id.name+" - "+installment.name)
        return result

    @api.onchange('discount_cash_total')
    def onchange_discount_cash(self):
        if self.discount_cash_total>0:
            self.discount_percent_total = 0.0

    @api.onchange('discount_percent_total')
    def onchange_discount_percent(self):
        if self.discount_percent_total>0:
            self.discount_cash_total = 0.0

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
        voucher_obj = self.env['account.payment']
        payment_method= self.env.ref(
            'account.account_payment_method_manual_out')
        vals= {
            'journal_id': self.journal.id,
            'payment_type': 'inbound',
            'date': self.payment_date,
            'amount': self.amount,
            'payment_method_id': payment_method.id,
            'partner_type': 'customer',
            'ref': self.communication,
        }
        installment_id = self.env.context.get('active_id')
        model = self.env.context.get('active_model')
        if model == 'loan.line.rs.own':
            installment = self.env['loan.line.rs.own'].sudo().browse(installment_id)
            if self.amount>installment.total_remaining_amount:
                raise UserError(_('You cannot pay more than the required amount!'))
            vals['partner_id']=installment.contract_partner_id.id
            vals['ownership_line_id']= installment.id
            installment.write({'total_paid_amount': installment.total_paid_amount+self.amount})

        if model == 'loan.line.rs.rent':
            installment = self.env['loan.line.rs.own'].sudo().browse(installment_id)
            vals['partner_id']=installment.contract_partner_id.id
            vals['rental_line_id']= installment.id
            installment.write({'total_paid_amount': installment.total_paid_amount+self.amount})

        voucher_id = voucher_obj.create(vals)
        voucher_id.action_post()
        return {
            'name': _('Voucher'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [voucher_id.id])],
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        return True