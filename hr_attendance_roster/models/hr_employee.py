from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    default_shift_id = fields.Many2one('attendance.shift.master', string='Default Shift')
    attendance_policy_id = fields.Many2one('hr.attendance.policy', string='Attendance Policy')
