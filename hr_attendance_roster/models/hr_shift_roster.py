from odoo import models, fields, api

class HrShiftRoster(models.Model):
    _name = 'hr.shift.roster'
    _description = 'Shift Roster'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    shift_id = fields.Many2one('attendance.shift.master', string='Assigned Shift', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        return super(HrShiftRoster, self).create(vals_list)
