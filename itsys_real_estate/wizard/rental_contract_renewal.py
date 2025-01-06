# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class rental_contract_renewal(models.TransientModel):
    _name = 'rental.contract.renewal'

    date_from= fields.Date    ('From Date', required=True)
    date_to= fields.Date    ('To Date', required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if self.filtered(lambda c: c.date_to and c.date_from > c.date_to):
            raise ValidationError(_('Contract start date must be less than contract end date.'))

    def confirm_renewal(self):
        rental_pool=  self.env['rental.contract']
        contract = rental_pool.browse(self._context.get('active_id'))
        copied= contract.copy()
        copied.write({'date_from':self.date_from,'date_to':self.date_to,'origin':contract.name})
        contract.write({'state':'renew'})

        return {
            'name': _('Rental Contract'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'rental.contract',
            'res_id': copied.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }