# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def create_new_journal_seqs(env):
    # env = api.Environment(env, SUPERUSER_ID, {})
    all_journal = env["account.journal"].with_context(active_test=False).search([])
    for one_journal in all_journal:
        all_vals = {}
        one_journal_vals = {
            "code": one_journal.code,
            "name": one_journal.name,
            "company_id": one_journal.company_id.id,
        }
        seq_vals = one_journal.prepare_new_sequence(one_journal_vals)
        all_vals["seq_id"] = env["ir.sequence"].create(seq_vals).id
        if one_journal.type in ("sale", "purchase") and one_journal.refund_sequence:
            rseq_vals = one_journal.prepare_new_sequence(one_journal_vals, refund=True)
            all_vals["seq_refund_id"] = env["ir.sequence"].create(rseq_vals).id
        one_journal.write(all_vals)
    return
