# Copyright 2018 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from email.policy import default
from odoo import api, fields, models, _
from num2words import num2words


class Partner(models.Model):
    
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    company_registeration = fields.Char('سجل الشركة ', default='000000000000')
    district = fields.Char(string="District")
    
class Company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'
    
    text_amount_language_currency = fields.Selection([('en', 'English'),
                                                      ('ar', 'Arabic'),
                                                      ('cz ', 'Czech'),
                                                      ('de', 'German'),
                                                      ('dk', 'Danish'),
                                                      ('en_GB', 'English - Great Britain'),
                                                      ('en_IN', 'English - India'),
                                                      ('es', 'Spanish'),
                                                      ('es_CO', 'Spanish - Colombia'),
                                                      ('es_VE', 'Spanish - Venezuela'),
                                                      ('eu', 'EURO'),
                                                      ('fi', 'Finnish'),
                                                      ('fr', 'French'),
                                                      ('fr_CH', 'French - Switzerland'),
                                                      ('fr_BE', 'French - Belgium'),
                                                      ('fr_DZ', 'French - Algeria'),
                                                      ('he', 'Hebrew'),
                                                      ('id', 'Indonesian'),
                                                      ('it', 'Italian'),
                                                      ('ja', 'Japanese'),
                                                      ('ko', 'Korean'),
                                                      ('lt', 'Lithuanian'),
                                                      ('lv', 'Latvian'),
                                                      ('no', 'Norwegian'),
                                                      ('pl', 'Polish'),
                                                      ('pt', 'Portuguese'),
                                                      ('pt_BR', 'Portuguese - Brazilian'),
                                                      ('sl', 'Slovene'),
                                                      ('sr', 'Serbian'),
                                                      ('ro', 'Romanian'),
                                                      ('ru', 'Russian'),
                                                      ('sl', 'Slovene'),
                                                      ('tr', 'Turkish'),
                                                      ('th', 'Thai'),
                                                      ('vi', 'Vietnamese'),
                                                      ('nl', 'Dutch'),
                                                      ('uk', 'Ukrainian'),
                                                      ], string='Text amount language/currency')


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    text_amount_language_currency = fields.Selection(related="company_id.text_amount_language_currency",
                                                     string='language_currency', readonly=False)

    @api.onchange('text_amount_language_currency')
    def save_text_amount_language_currency(self):
        if self.text_amount_language_currency:
            self.company_id.text_amount_language_currency = self.text_amount_language_currency
            
            
            
    
    partner_id = fields.Many2one('res.partner')
    company_registeration = fields.Char(related = 'partner_id.company_registeration')
    
    
    
    
class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'
      
class PromissoryNote(models.Model):
    
    _name = "promissory.note"
    
    issuer = fields.Many2one('res.partner', string='Issuer ')
    # reference = fields.Char(string="promissory Refrence", required=True, copy=False, readonly=True, default=lambda self: _('NEW'))
    reference = fields.Char(string='promissory Refrence', required=True, readonly=True, default=lambda self: _('New'))
    issuer_id = fields.Char(related='issuer.student_id.id_number', string=' Identification' , index=True)
    issuer_id_nationality = fields.Char(related='issuer.student_id.nationality.name', string=' Id ' , index=True)
    issuer_date = fields.Date(string=' Date ', index=True)
    payee = fields.Many2one('res.company', string='Company ', index=True)
    company_id = fields.Many2one('res.company', string='Company ' , default=1, index=True)
    payee_company_registeration  = fields.Char(related='company_id.partner_id.company_registeration', string='Company  ')
    invoice_no = fields.Many2one('account.move', string=' Invoice', domain=[("move_type", "!=", "entry")], index=True)
    partner_id = fields.Many2one('res.partner', string='  Partner', index=True)
    student_id = fields.Many2one('student.student', related="partner_id.student_id")
    partner_value = fields.Monetary(related='partner_id.total_due', string='  Balance ', index=True)    
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,                            
    readonly=True, states={'draft': [('readonly', False)]},
            default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.company)

    text_amoun3 = fields.Char(string="Amount in words   ", required=False, compute="amount_to_words3" )


    def get_default_calculation_method(self):
        default_calculation_method = '1'
        return default_calculation_method
   
    calculation_method = fields.Selection(
        string=' Calculation Type ',
        selection =[
                ('1','Partner Value'),
                ('2','Invoice Value'),
            ],
        default=get_default_calculation_method, 
        required=True
    )

    amount = fields.Float(   string="Amount",   digits="Account", default="", required=True,index=True ) # readonly=True,
    text_amount = fields.Char(string="   Amount in words", required=False, compute="amount_to_words" )
    text_amoun2 = fields.Char(string="   Amoount in words ", required=False, compute="amount_to_words2" )
    amount_residual = fields.Char(string=" Residual Value",  required=False, compute="compute_amount_residual")

    # @api.depends('invoice_no')
    def compute_amount_residual(self):
        for rec in self:
            rec['amount_residual'] = rec.invoice_no.amount_residual

    @api.depends('amount')
    def amount_to_words(self):
        for rec in self:
            if rec.amount:
                if rec.company_id.text_amount_language_currency:
                    rec.text_amount = num2words(rec.amount, to='currency', lang=rec.company_id.text_amount_language_currency)
                else:
                    rec.text_amount = num2words(rec.amount, to='currency', lang='ar')
            else:
                rec.text_amount = "صفر"

#---------------------------------------------------------------------------------------------------------------
    @api.depends('partner_id', 'partner_value','calculation_method','invoice_no')
    def amount_to_words3(self):
        from num2words import num2words
        
        partner_value_1 = self.partner_value
        if partner_value_1:
                
            pre = float(partner_value_1)
            text = ''
            entire_num = int((str(pre).split('.'))[0])
            decimal_num = int((str(pre).split('.'))[1])
            if decimal_num < 10:
                decimal_num = decimal_num * 10        
            text+=num2words(entire_num, lang='ar')
            text+=' ريال و '
            text+=num2words(decimal_num, lang='ar')
            text+=' هللة '

            # print text  
            
            self.text_amoun3 = text
        else:
            self.text_amoun3 = "صفر"
#---------------------------------------------------------------------------------------------------------------
    @api.depends('partner_id', 'partner_value','amount_residual', 'invoice_no','calculation_method')
    def amount_to_words2(self):
        from num2words import num2words
        
        if calculation_method == '1':
            amount_residual_1 = self.amount_residual
        else:
            amount_residual_1 = self.partner_value

        if amount_residual_1:
                
            pre = float(amount_residual_1)
            text = ''
            entire_num = int((str(pre).split('.'))[0])
            decimal_num = int((str(pre).split('.'))[1])
            if decimal_num < 10:
                decimal_num = decimal_num * 10        
            text+=num2words(entire_num, lang='ar')
            text+=' ريال و '
            text+=num2words(decimal_num, lang='ar')
            text+=' هللة '

            # print text  
            
            self.text_amoun2 = text
        else:
            self.text_amoun2 = "صفر"
#---------------------------------------------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'promissory.note') or _('New')
        res = super(PromissoryNote, self).create(vals)
        return res
    
        


