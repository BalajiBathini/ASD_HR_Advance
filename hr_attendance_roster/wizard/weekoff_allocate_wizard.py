from odoo import models, fields, api

class WeekoffAllocateWizard(models.TransientModel):
    _name = 'attendance.weekoff.allocate.wizard'
    _description = 'Bulk Allocate Weekly Offs'

    department_id = fields.Many2one('hr.department', string='Department', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    weekoff_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Weekly Off Day', required=True)
    date_from = fields.Date(string='Effective From', required=True, default=fields.Date.today)
    date_to = fields.Date(string='Effective To')

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.employee_ids = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])

    def action_allocate(self):
        weekoff_plan_env = self.env['attendance.weekoff.plan']
        for employee in self.employee_ids:
            weekoff_plan_env.create({
                'department_id': self.department_id.id,
                'employee_id': employee.id,
                'weekoff_day': self.weekoff_day,
                'date_from': self.date_from,
                'date_to': self.date_to
            })
        return {'type': 'ir.actions.act_window_close'}
