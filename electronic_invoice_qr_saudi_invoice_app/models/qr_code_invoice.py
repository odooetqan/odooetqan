# -*- coding: utf-8 -*-
import qrcode
import base64
from odoo import models, fields, api,_
from io import BytesIO
import binascii
try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None


class ResPartner(models.Model):
	_inherit = 'res.partner'

	additional_on = fields.Char('Additional No')
	sellername = fields.Char('Seller ID')

class ResCompany(models.Model):
	_inherit = 'res.company'

	additional_on = fields.Char('Additional No')
	sellername = fields.Char('Seller ID')
	company_name = fields.Char('Name')
	street1 = fields.Char()
	street2 = fields.Char()
	zip1 = fields.Char(change_default=True)
	city1 = fields.Char()
	state_id1 = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
	country_id1 = fields.Many2one('res.country', string='Country', ondelete='restrict')	

class generateQrCode():

	# this method will return image of qr with relevent url
	def generate_qr_code(url):
		qr = qrcode.QRCode(
			version=4,
			error_correction=qrcode.constants.ERROR_CORRECT_L,
			box_size=20,
			border=4,
			)
		qr.add_data(url)
		qr.make(fit=True)
		img = qr.make_image()
		temp = BytesIO()
		img.save(temp, format="PNG")
		qr_img = base64.b64encode(temp.getvalue())
		return qr_img

class QRCodeInvoice(models.Model):
	_inherit = 'account.move'

	qr_image = fields.Binary("QR Code", compute='_generate_qr_code')
	partner_vat = fields.Char(string='Partner Tax ID',related="partner_id.vat",store=True, index=True, help="The Parnter Tax Identification Number.")
	company_vat = fields.Char(string='Company Tax ID',related="company_id.vat",store=True, index=True, help="Your Company Tax Identification Number.")

	def amount_to_world(self,amount):
		return num2words(amount, lang="arabic")


	def amount_to_text(self,amount):
		words = num2words(amount)
		return words
	

	#conivert string value to hexa value
	def _string_to_hex(self, value):
		if value:
			string = str(value)
			string_bytes = string.encode("UTF-8")
			encoded_hex_value = binascii.hexlify(string_bytes)
			hex_value = encoded_hex_value.decode("UTF-8")
			return hex_value

	#for getting the hexa value
	def _get_hex(self, tag, length, value):
		if tag and length and value:
			hex_string = self._string_to_hex(value)
			length = len(value)
			conversion_table = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
			hexadecimal = ''
			while (length > 0):
				remainder = length % 16
				hexadecimal = conversion_table[remainder] + hexadecimal
				length = length // 16
			if len(hexadecimal) == 1:
				hexadecimal = "0" + hexadecimal
			return tag + hexadecimal + hex_string

	# Generate Qr Code In Binary Field
	def _generate_qr_code(self):
		if self.move_type in ('out_invoice', 'out_refund'):
			sellername = str(self.company_id.name)
			seller_vat_no = self.company_id.vat or ''
			if self.partner_id.company_type == 'company':
				customer_name = self.partner_id.name
				customer_vat = self.partner_id.vat
		else:
			sellername = str(self.partner_id.name)
			seller_vat_no = self.partner_id.vat
		seller_hex = self._get_hex("01", "0c", sellername) or ''
		vat_hex = self._get_hex("02", "0f", seller_vat_no) or ''
		time_stamp = str(self.create_date)
		date_hex = self._get_hex("03", "14", time_stamp) or ''
		total_with_vat_hex = self._get_hex("04", "0a", str(round(self.amount_total, 2))) or ''
		total_vat_hex = self._get_hex("05", "09", str(round(self.amount_tax, 2))) or ''
		qr_hex = "".join((p for p in (seller_hex,vat_hex,date_hex,total_with_vat_hex,total_vat_hex) if p))
		qr_info = base64.b64encode(bytes.fromhex(qr_hex)).decode()
		self.qr_image = generateQrCode.generate_qr_code(qr_info)

	def action_invoice_print(self):
		res = super().action_invoice_print()
		return self.env.ref('electronic_invoice_qr_saudi_invoice_app.report_ksa_invoice').report_action(self)
