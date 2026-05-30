from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    asd_daily_working_hours = fields.Float(
        related='company_id.asd_daily_working_hours', readonly=False,
        string='Daily Working Hours'
    )
    asd_weekly_offs_count = fields.Integer(
        related='company_id.asd_weekly_offs_count', readonly=False,
        string='Weekly Offs Count'
    )
    asd_carry_forward_enabled = fields.Boolean(
        related='company_id.asd_carry_forward_enabled', readonly=False,
        string='Enable Carry Forward'
    )
    asd_minimum_payable_hours = fields.Float(
        related='company_id.asd_minimum_payable_hours', readonly=False,
        string='Minimum Payable Hours'
    )
