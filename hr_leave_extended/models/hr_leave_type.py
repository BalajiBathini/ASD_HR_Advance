from odoo import models, fields

class HolidaysType(models.Model):
    _inherit = 'hr.leave.type'

    is_carry_forward = fields.Boolean("Carry Forward", default=False)
    carry_forward_max = fields.Integer("Max Carry Forward Days")
    is_encashable = fields.Boolean("Encashable", default=False)
    is_paid = fields.Boolean("Paid Leave", default=False)
