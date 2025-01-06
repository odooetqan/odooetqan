from odoo import api, fields, models

class PartnerInvoiceSummary(models.Model):
    _name = 'partner.invoice.summary'
    _description = 'Partner Invoice Summary'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    invoice_ids = fields.One2many('account.move', string='Invoices', compute='_compute_invoices')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount')
    


    @api.depends('partner_id')
    def _compute_invoices(self):
        for record in self:
            record.invoice_ids = self.env['account.move'].search([
                ('partner_id', '=', record.partner_id.id),
                ('move_type', 'in', ['out_invoice', 'in_refund']),
                ('state', '=', 'posted'),
            ])

    @api.depends('invoice_ids.amount_total')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.invoice_ids.mapped('amount_total'))
# ```

# Here, we create a new model `partner.invoice.summary` with the fields `partner_id`, `invoice_ids`, and `total_amount`. We use [computed fields](poe://www.poe.com/_api/key_phrase?phrase=computed%20fields&prompt=Tell%20me%20more%20about%20computed%20fields.) to retrieve the invoices and calculate the total amount.