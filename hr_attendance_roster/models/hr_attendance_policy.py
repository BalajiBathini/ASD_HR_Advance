from odoo import models, fields

class HrAttendancePolicy(models.Model):
    _name = 'hr.attendance.policy'
    _description = 'Attendance Policy'

    name = fields.Char(string='Policy Name', required=True)
    late_grace_period = fields.Float(string='Grace Period (Late)', help='Grace time in minutes before half day or late penalty applies', default=15.0)
    half_day_threshold = fields.Float(string='Half Day Threshold', help='Minimum hours to work to be considered Half Day', default=4.0)
    absent_threshold = fields.Float(string='Absent Threshold', help='Minimum hours to work to not be marked Absent', default=1.0)
    overtime_start_after = fields.Float(string='Overtime Start After', help='Hours beyond which time is counted as overtime', default=9.0)
    active = fields.Boolean(default=True)
