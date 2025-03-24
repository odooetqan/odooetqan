# -*- coding: utf-8 -*-
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date,timedelta

class Parser(models.AbstractModel):
	_name = 'report.itsys_real_estate.report_occupancy'

	def _get_units_status(self, region_ids, building_ids, unit_ids):
		units = []
		result=[]
		now = datetime.today().date()
		if unit_ids:
			for unit in unit_ids:
				units.append(unit)

		if building_ids:
			units_ids = self.env['product.template'].search([('is_property', '=', True),('building_id','in', building_ids)])
			for unit in units_ids:
				units.append(unit.id)

		if region_ids:
			building_ids = self.env['building'].search([('region_id','in', region_ids)])
			buildings=[]
			for b in building_ids: buildings.append(b.id)
			units_ids = self.env['product.template'].search([('is_property', '=', True),('building_id','in', buildings)])
			for unit in units_ids:
				units.append(unit.id)

		units = list(set(units))
		if len(units)==0:
			units_ids = self.env['product.template'].search([('is_property', '=', True)])
			for unit in units_ids:
				units.append(unit.id)

		rental_pool = self.env['rental.contract']
		for unit in units:
			unit_obj=self.env['product.template'].browse(unit)
			unit_line = {}
			unit_line['city']=None
			unit_line['region']=None
			unit_line['building']=None
			unit_line['type']=None
			unit_line['region'] = unit_obj.region_id.name
			unit_line['building'] = unit_obj.building_id.name
			unit_line['state'] = unit_obj.state
			unit_line['name'] = unit_obj.name
			if  unit_obj.state != 'free':
				rental_ids = rental_pool.search( [('building_unit', '=', unit)])
				rentals=[]
				for obj in rental_ids: rentals.append(obj.id)
				rentals = rental_pool.browse(rentals)
				if len(rentals) > 0:
					for rental in rentals:
						dates=[]
						for line in rental.loan_line:
							dates.append(line.date)
						if len(dates)>0:
							date_s=min(dates)
							date_e=max(dates)
							print (type(date_e),date_s,now,"***************************")
							# date_s = datetime.strptime(date_s, "%Y-%m-%d").date()
							# date_e = datetime.strptime(date_e, "%Y-%m-%d").date()

							if date_s <= now <= date_e:
								unit_line['rental']=''
							else:
								unit_line['type']='Rental'
								unit_line['rental']=rental.name
								unit_line['rental_date']=rental.date

			self.env.cr.execute("select name,date from ownership_contract where building_unit = "+str(unit)+" order by date desc")
			res = self.env.cr.dictfetchone()
			if res:
				unit_line['ownership'] = res['name']
				unit_line['ownership_date'] = res['date']
				unit_line['type']='Ownership'
			result.append(unit_line)
		return result


	@api.model
	def _get_report_values(self, docids, data=None):
		if not data.get('form'):
			raise UserError(_("Form content is missing, this report cannot be printed."))

		occupancy = self.env['ir.actions.report']._get_report_from_name('itsys_real_estate.report_occupancy')
		return {
			'doc_ids': self.ids,
			'doc_model': occupancy.model,
			'get_units_status': self._get_units_status( data['form']['region_ids'], data['form']['building_ids'], data['form']['unit_ids']),
		}

