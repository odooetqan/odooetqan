# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class account_journal(models.Model):
    _inherit = "account.journal"

    seq_id = fields.Many2one('ir.sequence', string='Entry Sequence', required=True, copy=False)
    next_seq_no = fields.Integer(string='Next Number', compute='_compute_sequence_number_next', inverse='_inverse_sequence_number_next')
    seq_refund_id = fields.Many2one('ir.sequence', string='Credit Note Entry Sequence', copy=False)
    next_refund_seq_no = fields.Integer(string='Credit Notes Next Number', compute='_compute_refund_sequence_number_next', inverse='_inverse_refund_sequence_number_next')

    @api.depends('seq_id.use_date_range', 'seq_id.number_next_actual')
    def _compute_sequence_number_next(self):
        for one_journal in self:
            if one_journal.seq_id:
                seq = one_journal.seq_id._get_current_sequence()
                one_journal.next_seq_no = seq.number_next_actual
            else:
                one_journal.next_seq_no = 1

    def _inverse_sequence_number_next(self):
        for one_journal in self:
            if one_journal.seq_id and one_journal.next_seq_no:
                seq = one_journal.seq_id._get_current_sequence()
                seq.sudo().number_next = one_journal.next_seq_no

    @api.depends('seq_refund_id.use_date_range', 'seq_refund_id.number_next_actual')
    def _compute_refund_sequence_number_next(self):
        for one_journal in self:
            if one_journal.seq_refund_id and one_journal.refund_sequence:
                seq = one_journal.seq_refund_id._get_current_sequence()
                one_journal.next_refund_seq_no = seq.number_next_actual
            else:
                one_journal.next_refund_seq_no = 1

    def _inverse_refund_sequence_number_next(self):
        for one_journal in self:
            if one_journal.seq_refund_id and one_journal.refund_sequence and one_journal.next_refund_seq_no:
                seq = one_journal.seq_refund_id._get_current_sequence()
                seq.sudo().number_next = one_journal.next_refund_seq_no

    @api.constrains("seq_refund_id", "seq_id")
    def _check_journal_sequence(self):
        for one_journal in self:
            if one_journal.seq_refund_id and one_journal.seq_id and one_journal.seq_refund_id == one_journal.seq_id:
                raise ValidationError(_("In journal '%s', the same sequence is used as Sequence and Credit Note Sequence.") % one_journal.display_name)

            if one_journal.seq_id and not one_journal.seq_id.company_id:
                raise ValidationError(_("Current Company is not set on sequence '%s' on journal '%s'.") % (one_journal.seq_id.display_name, one_journal.display_name))

            if one_journal.seq_refund_id and not one_journal.seq_refund_id.company_id:
                raise ValidationError(_("Currecnt Company is not set on sequence '%s' configured as credit note sequence of journal '%s'.") % (one_journal.seq_refund_id.display_name, one_journal.display_name))

    @api.model
    def create(self, vals):
        if not vals.get("seq_id"):
            vals["seq_id"] = self.create_new_seq(vals).id
        if (vals.get("type") in ("sale", "purchase") and vals.get("refund_sequence") and not vals.get("seq_refund_id")):
            vals["seq_refund_id"] = self.create_new_seq(vals, refund=True).id
        return super().create(vals)

    @api.model
    def prepare_new_sequence(self, vals, refund=False):
        code = vals.get("code") and vals["code"].upper() or ""
        prefix = "%s%s/%%(range_year)s/" % (refund and "R" or "", code)
        seq_vals = {
            "name": "%s %s" % (vals.get("name", _("Sequence")), refund and _("Refund") + " " or ""),
            "company_id": vals.get("company_id") or self.env.company.id,
            "implementation": "no_gap",
            "prefix": prefix,
            "padding": 4,
            "use_date_range": True,
        }
        return seq_vals

    @api.model
    def create_new_seq(self, vals, refund=False):
        seq_vals = self.prepare_new_sequence(vals, refund=refund)
        return self.env["ir.sequence"].sudo().create(seq_vals)


class account_move(models.Model):
    _inherit = "account.move"

    name = fields.Char(compute="_compute_name_by_journal_seq")

    @api.depends("state", "journal_id", "date")
    def _compute_name_by_journal_seq(self):
        for one_move in self:
           
            name = one_move.name or "/"
            if (one_move.state == "posted" and (not one_move.name or one_move.name == "/") and one_move.journal_id and one_move.journal_id.seq_id):
                if one_move.move_type in ("out_refund", "in_refund") and one_move.journal_id.type in ("sale", "purchase") and one_move.journal_id.refund_sequence and one_move.journal_id.seq_refund_id:
                    sequence = one_move.journal_id.seq_refund_id
                else:
                    sequence = one_move.journal_id.seq_id
                name = sequence.next_by_id(sequence_date=one_move.date)
            one_move.name = name

    def _constrains_date_sequence(self):
        return True

    create_date = fields.Datetime(readonly=False)
    
    # @api.onchange('invoice_date')
    # def action_post(self):
    #   for move in self:
    #     if move.invoice_date:
    #         move.write({'date': move.invoice_date})
    #         move._post()
    #     else:
    #         move.write({'date': move.create_date})
    #         move._post()
            
        

    # date = fields.Date(compute='_compute_create_date', store=True)

    # @api.depends('invoice_date')  
    # def _compute_create_date(self):
    #   for move in self:
    #     if move.invoice_date:
    #         move.date = move.invoice_date
    #         move._post()

    #     else:
    #         move.date = move.create_date
    #         move._post()
            
    # def action_post(self):
    #   for move in self:
    #     move._post()
