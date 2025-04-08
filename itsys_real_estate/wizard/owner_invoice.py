# -*- coding: utf-8 -*-
import time
import datetime
from dateutil import relativedelta
from odoo import fields, models, api,tools
from datetime import datetime
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

class owner_account_check(models.TransientModel):
    _name = 'owner.account.check'

    partner_id = fields.Many2one('res.partner', string="Owner",required=True,domain=[('is_owner', '=', True)])
    analytic_account_id = fields.Many2many('account.analytic.account')
    date_start= fields.Date('From',required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_end= fields.Date('To',required=True, default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    comm_percent= fields.Float('Commission Percentage', default=90.0)
    expense_line= fields.One2many('owner.expense', 'main_id')

    def create_owner_invoice(self):
        date_start= (self.date_start).strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_end= (self.date_end).strftime(DEFAULT_SERVER_DATE_FORMAT)
        domain = [('move_id.property_owner_id', '=', self.partner_id.id),
                                                    ('move_id.payment_state', '=', 'paid'),
                                                    ('move_id.invoice_date', '>=', date_start),
                                                    ('move_id.invoice_date', '<=', date_end),
                                                    ('move_id.move_type', '=', 'out_invoice'),
                                                    ('exclude_from_invoice_tab', '=', False),
                                                    ('commissioned', '=', False),
                                                    ]
        if self.analytic_account_id:
            domain.append(('analytic_account_id','in',self.analytic_account_id.ids))
        aml = self.env['account.move.line'].search(domain)
        invoice_amt=0.0
        invoice_comm=0.0
        for line in aml:
            invoice_amt+= line.price_total
            invoice_comm+= (line.price_total*self.comm_percent/100.0)
            line.commissioned= True
            print (line.price_total,self.comm_percent,"A"*200)
        account_move_obj = self.env['account.move']
        journal_pool = self.env['account.journal']
        journal = journal_pool.search([('type', '=', 'purchase')], limit=1)
        lines=[]
        if invoice_comm:
            label= (' From '+str(date_start)+' To '+ str(date_end))
            lines.append((0, None, {
                'name': _('Rental Collections'+label),
                'quantity': 1,
                'price_unit': invoice_comm,
            }))
            for ex in self.expense_line:
                lines.append((0, None, {
                    'name': ex.label,
                    'quantity': 1,
                    'price_unit': -ex.amount,
                }))
            invoice= account_move_obj.create({'journal_id': journal.id,
                                     'partner_id': self.partner_id.id,
                                     'move_type': 'in_invoice',
                                     'invoice_line_ids': lines
                                     })
            return {
                'name': _('Invoice'),
                'view_type': 'form',
                'res_id':invoice.id,
                'view_mode': 'form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
            }
        else:
            raise UserError(_('There are no customer invoices in this period!'))


class owner_expense(models.TransientModel):
    _name = 'owner.expense'

    main_id= fields.Many2one('owner.account.check',ondelete='cascade', readonly=True)
    amount= fields.Float('Amount',required=True)
    label= fields.Char('Label',required=True)
