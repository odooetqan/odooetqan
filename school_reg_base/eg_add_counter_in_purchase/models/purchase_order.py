from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "purchase.order"

    print_count = fields.Integer(string="Counter")

    def add_count(self):
        for account_id in self:
            account_id.print_count +=1
