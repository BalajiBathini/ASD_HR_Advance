# -*- coding: utf-8 -*-
from odoo import models, fields


class HrExitInterview(models.Model):
    _name = 'hr.exit.interview'
    _description = 'Exit Interview'

    exit_id = fields.Many2one('hr.exit', string='Exit Request', required=True, ondelete='cascade')
    employee_id = fields.Many2one(related='exit_id.employee_id', string='Employee', store=True)
    interviewer_id = fields.Many2one('res.users', string='Conducted By',
                                      default=lambda self: self.env.user)
    interview_date = fields.Date(string='Interview Date', default=fields.Date.context_today)

    reason = fields.Text(string='Primary Exit Reason')
    team_rating = fields.Selection([
        ('1', '1 - Very Poor'),
        ('2', '2 - Poor'),
        ('3', '3 - Average'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent'),
    ], string='Team Experience Rating')
    manager_rating = fields.Selection([
        ('1', '1 - Very Poor'),
        ('2', '2 - Poor'),
        ('3', '3 - Average'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent'),
    ], string='Manager Rating')
    suggestions = fields.Text(string='Suggestions / Feedback')
    rehire_eligible = fields.Boolean(string='Eligible for Rehire')
