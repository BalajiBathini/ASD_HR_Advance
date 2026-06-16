# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrExitClearanceTemplate(models.Model):
    _name = 'hr.exit.clearance.template'
    _description = 'Exit Clearance Checklist Template'

    name = fields.Char(string='Item', required=True)
    department = fields.Selection([
        ('it', 'IT'),
        ('finance', 'Finance'),
        ('admin', 'Admin'),
        ('hr', 'HR'),
    ], string='Department', required=True)
    sequence = fields.Integer(default=10)


class HrExitClearance(models.Model):
    _name = 'hr.exit.clearance'
    _description = 'Exit Clearance Checklist Line'
    _order = 'department, id'

    exit_id = fields.Many2one('hr.exit', string='Exit Request', required=True, ondelete='cascade')
    employee_id = fields.Many2one(related='exit_id.employee_id', string='Employee', store=True)

    department = fields.Selection([
        ('it', 'IT'),
        ('finance', 'Finance'),
        ('admin', 'Admin'),
        ('hr', 'HR'),
    ], string='Department', required=True)

    item = fields.Char(string='Checklist Item', required=True)

    status = fields.Selection([
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('na', 'N/A'),
    ], string='Status', default='pending', required=True)

    remarks = fields.Text(string='Remarks')
    cleared_by = fields.Many2one('res.users', string='Cleared By')
    cleared_date = fields.Date(string='Cleared Date')

    @api.onchange('status')
    def _onchange_status(self):
        for rec in self:
            if rec.status == 'cleared':
                rec.cleared_by = self.env.user
                rec.cleared_date = fields.Date.context_today(rec)
            else:
                rec.cleared_by = False
                rec.cleared_date = False
