# -*- coding: utf-8 -*-
from odoo import fields, models


class HrAppraisalFeedback(models.Model):
    _name = 'hr.appraisal.feedback'
    _description = '360 Degree Feedback'

    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade')
    employee_id = fields.Many2one(
        related='appraisal_id.employee_id', string='Employee', store=True)

    reviewer_id = fields.Many2one(
        'hr.employee', string='Reviewer (Peer/Subordinate)', required=True,
        help='Peer or subordinate invited to give feedback')
    reviewer_type = fields.Selection([
        ('peer', 'Peer'),
        ('subordinate', 'Subordinate'),
        ('other', 'Other'),
    ], string='Relationship', default='peer', required=True)

    state = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Submitted'),
    ], string='Status', default='pending')

    rating = fields.Selection([
        ('1', '1 - Needs Improvement'),
        ('2', '2 - Below Average'),
        ('3', '3 - Average'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent'),
    ], string='Rating')

    feedback = fields.Html(string='Feedback')
    submitted_date = fields.Date(string='Submitted On')

    def action_mark_submitted(self):
        self.write({
            'state': 'done',
            'submitted_date': fields.Date.context_today(self),
        })
