from odoo import models, fields, api

class AttendanceWeekoffPlan(models.Model):
    _name = 'attendance.weekoff.plan'
    _description = 'Weekly Off Plan'
    
    department_id = fields.Many2one('hr.department', string='Department')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    weekoff_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Weekly Off Day', required=True)
    date_from = fields.Date(string='Effective From', required=True)
    date_to = fields.Date(string='Effective To')
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
