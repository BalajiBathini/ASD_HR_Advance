from odoo import models, fields

class AttendanceShiftMaster(models.Model):
    _name = 'attendance.shift.master'
    _description = 'Shift Master'

    name = fields.Char(string='Shift Name', required=True)
    code = fields.Char(string='Shift Code', required=True, help="e.g. P1, P2, PG")
    start_time = fields.Float(string='Start Time', required=True)
    end_time = fields.Float(string='End Time', required=True)
    shift_type = fields.Selection([
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('night', 'Night'),
        ('rotational', 'Rotational')
    ], string='Shift Type', default='morning', required=True)
    grace_time = fields.Float(string='Grace Time')
    working_hours = fields.Float(string='Working Hours', required=True)
    active = fields.Boolean(default=True)
