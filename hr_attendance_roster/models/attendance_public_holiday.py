from odoo import models, fields

class AttendancePublicHoliday(models.Model):
    _name = 'attendance.public.holiday'
    _description = 'Public Holiday'

    name = fields.Char(string='Holiday Name', required=True)
    date = fields.Date(string='Date', required=True)
    department_id = fields.Many2one('hr.department', string='Applicable Department', help="Leave blank if applicable to all departments")
    company_id = fields.Many2one('res.company', string='Applicable Company', default=lambda self: self.env.company)
