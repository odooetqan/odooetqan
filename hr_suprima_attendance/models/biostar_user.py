from odoo import api, fields, models

class BiostarUser(models.Model):
    _name = "biostar.user"
    _description = "BioStar User"

    name = fields.Char(required=True)
    device_id = fields.Many2one("biostar.device", required=True, ondelete="cascade")
    biostar_user_id = fields.Char(required=True, index=True)
    card_no = fields.Char()

    employee_id = fields.Many2one("hr.employee", string="Linked Employee",
                                  help="Link to employee (barcode should match BioStar user/card if you prefer auto)")
    employee_barcode = fields.Char(related="employee_id.barcode", store=False)
