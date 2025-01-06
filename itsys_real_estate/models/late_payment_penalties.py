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
from datetime import datetime, date,timedelta
from odoo.exceptions import UserError
from odoo.tools.translate import _

class late_payment_penalties(models.Model):
    _name = "late.payment.penalties"
    
    region= fields.Many2one('regions','Region', )
    percent= fields.Integer ('Penalty Percentage')
    account= fields.Many2one('account.account','Account', )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)


    def get_account(self):
        penalty_account = self.env['res.config.settings'].browse(self.env['res.config.settings'].search([])[-1].id).penalty_account.id if self.env['res.config.settings'].search([]) else ""
        if not penalty_account:
            raise UserError(_('Please set default Discount Account!'))
        return penalty_account

    def get_penalties(self,line):
        line_date=line.date
        diff = (date.today().year - line_date.year)*12 + date.today().month - line_date.month
        if diff>0:
            penalty_percent = self.env['res.config.settings'].browse(
                self.env['res.config.settings'].search([])[-1].id).penalty_percent if self.env[
                'res.config.settings'].search([]) else ""
            if not penalty_percent:
                raise UserError(_('Please set default Penalty Percentage!'))

            result = line.amount*penalty_percent*diff/100.0
            return result
        else:
            return 0