from odoo import models, fields, api


class HrOnboardingTemplate(models.Model):
    _name = 'hr.onboarding.template'
    _description = 'Onboarding Template'
    _order = 'name'

    name = fields.Char(
        string='Template Name',
        required=True,
        help='e.g. "Standard Onboarding", "IT Hire Onboarding"',
    )
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    task_line_ids = fields.One2many(
        'hr.onboarding.template.line',
        'template_id',
        string='Checklist Tasks',
        copy=True,
    )
    task_count = fields.Integer(
        string='Tasks',
        compute='_compute_task_count',
    )

    @api.depends('task_line_ids')
    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_line_ids)


class HrOnboardingTemplateLine(models.Model):
    _name = 'hr.onboarding.template.line'
    _description = 'Onboarding Template Task Line'
    _order = 'due_days, sequence'

    template_id = fields.Many2one(
        'hr.onboarding.template',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Task Name', required=True)
    category = fields.Selection(
        selection=[
            ('it', 'IT Setup'),
            ('hr_admin', 'HR Admin'),
            ('payroll', 'Payroll'),
            ('training', 'Training'),
            ('manager', 'Manager'),
        ],
        string='Category',
        required=True,
    )
    responsible_role = fields.Selection(
        selection=[
            ('it_team', 'IT Team'),
            ('hr_admin', 'HR Admin'),
            ('employee', 'Employee'),
            ('payroll_team', 'Payroll Team'),
            ('ld_team', 'L&D Team'),
            ('manager', 'Manager'),
        ],
        string='Default Responsible',
        required=True,
    )
    due_days = fields.Integer(
        string='Due (Days from Join)',
        default=0,
        help='0 = Day 0 (Joining Day)',
    )
    description = fields.Text(string='Task Instructions')
    is_mandatory = fields.Boolean(string='Mandatory', default=True)
