# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import base64
from num2words import num2words
from odoo import api, fields, models, _
# from odoo.tools.misc import get_lang
# from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_date_supply = fields.Datetime('Date Of Supply')

    # def action_invoice_tax_report(self, type):
    #     self.ensure_one()
    #     if type == 'tax_invoice':
    #         template = self.env.ref('saudi_einvoice_knk.email_template_edi_invoice_tax_etir', raise_if_not_found=False)
    #     elif type == 'simplified_tax_invoice':
    #         template = self.env.ref('saudi_einvoice_knk.email_template_edi_invoice_etir', raise_if_not_found=False)
    #     lang = False
    #     if template:
    #         lang = template._render_lang(self.ids)[self.id]
    #     if not lang:
    #         lang = get_lang(self.env).code
    #     compose_form = self.env.ref('account.account_move_send_form', raise_if_not_found=False)
    #     ctx = dict(
    #         default_model='account.move',
    #         default_res_id=self.id,
    #         active_ids=[self.id],
    #         default_res_model='account.move',
    #         default_use_template=bool(template),
    #         default_template_id=template and template.id or False,
    #         default_composition_mode='comment',
    #         mark_invoice_as_sent=True,
    #         custom_layout="mail.mail_notification_paynow",
    #         model_description=self.with_context(lang=lang).type_name,
    #         force_email=True
    #     )
    #     return {
    #         'name': _('Send Invoice'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'account.invoice.send',
    #         'views': [(compose_form.id, 'form')],
    #         'view_id': compose_form.id,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def get_product_arabic_name(self, pid):
        IrTranslation = self.env['ir.translation']
        domain = [
            ('name', '=', 'product.product,name'), ('state', '=', 'translated')]
        translation = IrTranslation.search(domain + [('res_id', '=', pid)])
        if translation:
            return translation.value
        else:
            product = self.env['product.product'].browse(int(pid))
            translation = IrTranslation.search(domain + [('res_id', '=', product.product_tmpl_id.id)])
            if translation:
                return translation.value
        return ''

    def amount_word(self, amount):
        language = self.partner_id.lang or 'en'
        language_id = self.env['res.lang'].search([('code', '=', 'ar_AA')])
        if language_id:
            language = language_id.iso_code
        amount_str = str('{:2f}'.format(amount))
        amount_str_splt = amount_str.split('.')
        before_point_value = amount_str_splt[0] 
        after_point_value = amount_str_splt[1][:2]
        before_amount_words = num2words(int(before_point_value), lang=language) 
        after_amount_words = num2words(int(after_point_value), lang=language) 
        amount = before_amount_words+' ' + 'ريال' + ' و ' + after_amount_words + '  ' +  'هلله'
        return amount

    def _amount_total_words(self, amount):
        words_amount = self.currency_id.amount_to_text(amount)
        return words_amount

    @api.model
    def get_qr_code(self):
        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array
        for record in self:
            qr_code_str = ''
            seller_name_enc = get_qr_encoding(1, record.company_id.display_name)
            company_vat_enc = get_qr_encoding(2, record.company_id.vat or '')
            # date_order = fields.Datetime.from_string(record.create_date)
            if record.invoice_date_supply:
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.invoice_date_supply)
            else:
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.create_date)
            timestamp_enc = get_qr_encoding(3, time_sa.isoformat())
            invoice_total_enc = get_qr_encoding(4, str(record.amount_total))
            total_vat_enc = get_qr_encoding(5, str(record.currency_id.round(record.amount_total - record.amount_untaxed)))

            str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
            qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            return qr_code_str

    # def action_send_and_print(self):
    #     template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
    #     if template.attachment_ids:
    #         template.attachment_ids = False
    #     result, format = self.env["ir.actions.report"]._render_qweb_pdf(
    #         "saudi_einvoice_knk.action_report_tax_invoice", [self.id]
    #     )
    #     data_record = base64.b64encode(result)
    #     ir_values = {
    #         'name': ('Saudi VAT Invoice - %s') % self.name,
    #         'type': 'binary',
    #         'datas': data_record,
    #         'store_fname': data_record,
    #         'mimetype': 'application/pdf',
    #         'res_model': 'account.move',
    #     }
    #     report_attachment = self.env['ir.attachment'].sudo().create(ir_values)
    #     new_result, format = self.env["ir.actions.report"]._render_qweb_pdf(
    #         "saudi_einvoice_knk.action_report_simplified_tax_invoice", [self.id]
    #     )
    #     new_data_record = base64.b64encode(new_result)
    #     new_ir_values = {
    #         'name': ('Simplified VAT Invoice - %s') % self.name,
    #         'type': 'binary',
    #         'datas': new_data_record,
    #         'store_fname': new_data_record,
    #         'mimetype': 'application/pdf',
    #         'res_model': 'account.move',
    #     }
    #     new_report_attachment = self.env['ir.attachment'].sudo().create(new_ir_values)

    #     if template and not template.attachment_ids:
    #         template.attachment_ids = [(4, report_attachment.id), (4, new_report_attachment.id)]

    #     if any(not x.is_sale_document(include_receipts=True) for x in self):
    #         raise UserError(_("You can only send sales documents"))

    #     return {
    #         'name': _("Send"),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'account.move.send',
    #         'target': 'new',
    #         'context': {
    #             'active_ids': self.ids,
    #             'default_mail_template_id': template and template.id or False,
    #         },
    #     }


class ResCompany(models.Model):
    _inherit = 'res.company'

    arabic_name = fields.Char('Arabic Name')
    arabic_street = fields.Char('Arabic Street')
    arabic_street2 = fields.Char('Arabic Street2')
    arabic_city = fields.Char('Arabic City')
    arabic_state = fields.Char('Arabic State')
    arabic_country = fields.Char('Arabic Country')
    arabic_zip = fields.Char('Arabic Zip')
    invoice_note = fields.Char('Invoice Notes')


class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'
    _description = "Account Move Send"

    @api.depends('mail_template_id')
    def _compute_mail_attachments_widget(self):
        for wizard in self:
            wizard.mail_attachments_widget = []
            if wizard.mode == 'invoice_single':
                manual_attachments_data = [x for x in wizard.mail_attachments_widget or [] if x.get('custom_field')]
                if wizard.mail_template_id and wizard.mail_template_id.name == 'Invoice Tax: Send by email':
                    # attachment_id = self.env.ref('saudi_einvoice_knk.action_report_tax_invoice')
                    # if attachment_id:
                    #     if wizard.mail_template_id.attachment_ids:
                    #         wizard.mail_template_id.attachment_ids.unlink()
                    result, format = self.env["ir.actions.report"].sudo()._render_qweb_pdf("saudi_einvoice_knk.action_report_tax_invoice", res_ids=wizard.move_ids.ids)
                    data_record = base64.b64encode(result)
                    ir_values = {
                        # 'name': 'Saudi VAT Invoice',
                        'name': 'Saudi VAT Invoice.pdf',
                        'type': 'binary',
                        'datas': data_record,
                        'store_fname': data_record,
                        'mimetype': 'application/pdf',
                        'res_model': 'account.move',
                        'res_id': wizard.move_ids.ids[0],
                    }
                    report_attachment = self.env['ir.attachment'].sudo().create(ir_values)
                    # if wizard.mail_template_id and not wizard.mail_template_id.attachment_ids:
                    #     wizard.mail_template_id.attachment_ids = [(4, report_attachment.id)]
                    wizard.mail_template_id.attachment_ids = [(6, 0, report_attachment.ids)]
                    wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
                    # else:
                    #     wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
                else:
                    wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
                if wizard.mail_template_id and wizard.mail_template_id.name == 'Invoice Simplified Tax : Send by email':
                    # attachment_id = self.env.ref('saudi_einvoice_knk.action_report_simplified_tax_invoice')
                    # if attachment_id:
                    #     if wizard.mail_template_id.attachment_ids:
                    #         wizard.mail_template_id.attachment_ids.unlink()
                    new_result, format = self.env["ir.actions.report"].sudo()._render_qweb_pdf("saudi_einvoice_knk.action_report_simplified_tax_invoice", res_ids=wizard.move_ids.ids)
                    data_record = base64.b64encode(new_result)
                    ir_values = {
                        # 'name': 'Saudi Simplified VAT Invoice',
                        'name': 'Saudi Simplified VAT Invoice.pdf',
                        'type': 'binary',
                        'datas': data_record,
                        'store_fname': data_record,
                        'mimetype': 'application/pdf',
                        'res_model': 'account.move',
                        'res_id': wizard.move_ids.ids[0],
                    }
                    new_report_attachment = self.env['ir.attachment'].sudo().create(ir_values)
                    # if wizard.mail_template_id and not wizard.mail_template_id.attachment_ids:
                    #     wizard.mail_template_id.attachment_ids = [(4, new_report_attachment.id)]
                    wizard.mail_template_id.attachment_ids = [(6, 0, new_report_attachment.ids)]
                    wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
                    # else:
                    #     wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
                else:
                    wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
            else:
                wizard.mail_attachments_widget = []

    # @api.depends('mail_template_id')
    # def _compute_mail_attachments_widget(self):
    #     for wizard in self:
    #         if wizard.mode == 'invoice_single':
    #             manual_attachments_data = [x for x in wizard.mail_attachments_widget or [] if x.get('manual')]
    #             if wizard.mail_template_id.name == 'Invoice Tax: Send by email':
    #                 # move_ids_tuple = tuple(wizard.move_ids.ids)
    #                 # pdf_report_data, format = self.env["ir.actions.report"]._render_qweb_pdf(
    #                 #     "saudi_einvoice_knk.action_report_tax_invoice", [wizard.move_ids.id]
    #                 # )
    #                 pdf_report_data, format = self.env["ir.actions.report"].sudo()._render_qweb_pdf("saudi_einvoice_knk.action_report_tax_invoice", res_ids=wizard.move_ids.ids)
    #                 # pdf_report_data = self.env["ir.actions.report"].sudo()._render_qweb_pdf("saudi_einvoice_knk.action_report_tax_invoice", res_ids=wizard.move_ids.ids)
    #                 # pdf_list = list(pdf_report_data)
    #                 # if isinstance(pdf_list, list) and pdf_list:
    #                 if pdf_report_data:
    #                     data_record = base64.b64encode(pdf_report_data)
    #                     # pdf_data_str = base64.b64encode(pdf_report_data).decode('utf-8')
    #                     pdf_report_attachment = {
    #                         'name': 'Saudi VAT Invoice',
    #                         'type': 'binary',
    #                         'datas': data_record,
    #                         'store_fname': data_record,
    #                         'mimetype': 'application/pdf',
    #                         'res_model': 'account.move',
    #                         'res_id': wizard.move_ids.ids[0],
    #                     }
    #                     report_attachment = self.env['ir.attachment'].sudo().create(pdf_report_attachment)
    #                     if wizard.mail_template_id and not wizard.mail_template_id.attachment_ids:
    #                         wizard.mail_template_id.attachment_ids = [(4, report_attachment.id)]
    #                     wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
    #                 else:
    #                     wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
    #             else:
    #                 wizard.mail_attachments_widget = self._get_default_mail_attachments_widget(wizard.move_ids, wizard.mail_template_id) + manual_attachments_data
    #         else:
    #             wizard.mail_attachments_widget = []
