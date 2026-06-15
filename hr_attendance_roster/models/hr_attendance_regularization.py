from odoo import models, fields, api, exceptions

class HrAttendanceRegularization(models.Model):
    _name = 'hr.attendance.regularization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Attendance Regularization Request'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id)
    attendance_id = fields.Many2one('hr.attendance', string='Original Attendance')
    regularize_date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    
    check_in = fields.Datetime(string='Requested Check In', required=True)
    check_out = fields.Datetime(string='Requested Check Out', required=True)
    
    reason = fields.Text(string='Reason', required=True)
    
    manager_id = fields.Many2one('hr.employee', string='Approving Manager', related='employee_id.parent_id', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_approve(self):
        for rec in self:
            # Create or update attendance record
            if rec.attendance_id:
                rec.attendance_id.write({
                    'check_in': rec.check_in,
                    'check_out': rec.check_out,
                })
            else:
                self.env['hr.attendance'].create({
                    'employee_id': rec.employee_id.id,
                    'check_in': rec.check_in,
                    'check_out': rec.check_out,
                })
            rec.state = 'approved'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

    @api.constrains('check_in', 'check_out')
    def _check_time_validity(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_in >= rec.check_out:
                raise exceptions.ValidationError('Check-out must be strictly after Check-in.')
