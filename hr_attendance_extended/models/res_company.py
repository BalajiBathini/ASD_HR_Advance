from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    asd_daily_working_hours = fields.Float(string='Daily Working Hours', default=8.0)
    asd_weekly_offs_count = fields.Integer(string='Weekly Offs Count', default=4)
    asd_carry_forward_enabled = fields.Boolean(string='Enable Carry Forward', default=True)
    asd_minimum_payable_hours = fields.Float(string='Minimum Payable Hours', default=0.0)
