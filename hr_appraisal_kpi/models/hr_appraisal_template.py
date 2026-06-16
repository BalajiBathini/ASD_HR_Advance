# -*- coding: utf-8 -*-
from odoo import fields, models


class HrAppraisalTemplate(models.Model):
    _name = 'hr.appraisal.template'
    _description = 'Appraisal Template'

    name = fields.Char(string='Template Name', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    employee_feedback_template = fields.Html(
        string='Employee Self Assessment Questions',
        help='Default questionnaire shown to the employee '
             '(e.g. My Work, My Future, My Feelings sections)')
    manager_feedback_template = fields.Html(
        string='Manager Feedback Questions',
        help='Default questionnaire shown to the manager '
             '(e.g. Feedback, Evaluation, Improvements sections)')

    default_kra_line_ids = fields.One2many(
        'hr.appraisal.template.kra', 'template_id', string='Default KRAs')

    note = fields.Text(string='Notes')


class HrAppraisalTemplateKra(models.Model):
    _name = 'hr.appraisal.template.kra'
    _description = 'Default KRA Line in Appraisal Template'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'hr.appraisal.template', string='Template', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='KRA Description', required=True)
    weightage = fields.Float(string='Default Weightage (%)', default=0.0)
