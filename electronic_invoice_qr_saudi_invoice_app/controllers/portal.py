# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class PortalAccount(CustomerPortal):

	@http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
	def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
		try:
			invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
		except (AccessError, MissingError):
			return request.redirect('/my')

		if report_type in ('html', 'pdf', 'text'):
			return self._show_report(model=invoice_sudo, report_type=report_type, report_ref='electronic_invoice_qr_saudi_invoice_app.report_ksa_invoice', download=download)

		values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
		acquirers = values.get('acquirers')
		if acquirers:
			country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
			values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual, invoice_sudo.currency_id, country_id)

		return request.render("account.portal_invoice_page", values)