# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class rental_contract_bi_report(models.Model):
    _name = "report.rental.contract.bi"
    _description = "Rental Contracts Statistics"
    _auto = False
    contract_date= fields.Date('Contract Date', readonly=True)
    due_date= fields.Date('Due Date', readonly=True)
    name= fields.Char('Contract', readonly=True)
    partner_id= fields.Many2one('res.partner', 'Partner', readonly=True)
    user_id= fields.Many2one('res.users', 'Responsible', readonly=True)
    contract_unit= fields.Many2one('product.template', 'Property', readonly=True)
    contract_building= fields.Many2one('building', 'Building', readonly=True)
    contract_region= fields.Many2one('regions', 'Region', readonly=True)
    paid= fields.Float('Paid Amount', readonly=True)
    unpaid= fields.Float('Balance', readonly=True)
    amount= fields.Float('Amount', digits=(16, 4), readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    payment_state = fields.Selection([
                        ('not_paid', 'Not Paid'),
                        ('in_payment', 'In Payment'),
                        ('paid', 'Paid'),
                        ('partial', 'Partially Paid'),
                        ('reversed', 'Reversed'),
                        ('invoicing_legacy', 'Invoicing App Legacy'),
                          ],'Payment State', readonly=True)
    invoice_state = fields.Selection([('draft', 'Draft'),
                                    ('posted', 'Posted'),
                                    ('cancel', 'Cancelled')], readonly=True)

    state= fields.Selection([('draft','Draft'),
                               ('confirmed','Confirmed'),
                               ('cancel','Canceled')
                               ], 'State')

    _order = 'contract_date asc'

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_rental_contract_bi')
        self._cr.execute("""
            create or replace view report_rental_contract_bi as (
                select min(lro.id) as id,
                oc.name, 
                oc.date as contract_date, 
                oc.partner_id as partner_id, 
                oc.building_unit as contract_unit, 
                oc.building as contract_building,
                oc.region as contract_region, 
                lro.date as due_date,
                oc.state as state,
		        oc.user_id as user_id,
                (lro.amount-am.amount_residual) as paid,                 
                am.amount_residual as unpaid,	 
                lro.invoice_id as invoice_id,	    
                am.payment_state as payment_state,	    
                am.state as invoice_state,	                    
                lro.amount as amount
                FROM rental_contract oc 
                LEFT JOIN loan_line_rs_rent lro ON oc.id = lro.loan_id
                LEFT JOIN account_move am ON am.id= lro.invoice_id
                GROUP BY
                    oc.state,
                    lro.paid, 
                    lro.amount, 
                    am.amount_residual, 
                    am.state,
                    am.payment_state ,
                    lro.invoice_id,                    
                    oc.name, 
                    oc.partner_id, 
                    oc.building_unit, 
                    oc.building, 
                    oc.region, 
                    oc.date, 
                    lro.date,
                    oc.user_id           
           )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: