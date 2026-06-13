from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrOnboardingTask(models.Model):
    _name = 'hr.onboarding.task'
    _description = 'Onboarding Task'
    _inherit = ['mail.thread']
    _order = 'due_days, sequence, id'

    # ─── Core Fields ────────────────────────────────────────────────────────

    onboarding_id = fields.Many2one(
        'hr.onboarding',
        string='Onboarding Plan',
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        related='onboarding_id.employee_id',
        string='Employee',
        store=True,
        readonly=True,
    )
    join_date = fields.Date(
        related='onboarding_id.join_date',
        string='Join Date',
        store=True,
        readonly=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Task', required=True)
    description = fields.Text(string='Instructions')
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
        string='Role',
    )
    responsible_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True,
    )
    due_days = fields.Integer(
        string='Due (Day)',
        help='Day number from joining (0 = joining day)',
    )
    due_date = fields.Date(
        string='Due Date',
        compute='_compute_due_date',
        store=True,
        readonly=False,  # Allow manual override
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('skipped', 'Skipped'),
        ],
        string='Status',
        default='pending',
        tracking=True,
    )
    is_mandatory = fields.Boolean(string='Mandatory', default=True)
    completed_date = fields.Date(string='Completed On', readonly=True, copy=False)
    completed_by = fields.Many2one(
        'res.users',
        string='Completed By',
        readonly=True,
        copy=False,
    )
    ticket_ref = fields.Char(
        string='IT Ticket Ref',
        help='Reference to IT helpdesk ticket (if applicable)',
    )
    notes = fields.Text(string='Completion Notes')
    color = fields.Integer(compute='_compute_color')

    # ─── Computes ────────────────────────────────────────────────────────────

    @api.depends('onboarding_id.join_date', 'due_days')
    def _compute_due_date(self):
        from datetime import timedelta
        for task in self:
            if task.join_date and task.due_days is not False:
                task.due_date = task.join_date + timedelta(days=task.due_days)
            else:
                task.due_date = False

    def _compute_color(self):
        today = fields.Date.today()
        for task in self:
            if task.state == 'done':
                task.color = 10  # Green
            elif task.state == 'skipped':
                task.color = 8   # Teal
            elif task.due_date and task.due_date < today:
                task.color = 1   # Red (Overdue)
            elif task.due_date and task.due_date == today:
                task.color = 2   # Orange (Due today)
            else:
                task.color = 0   # Default

    # ─── Actions ─────────────────────────────────────────────────────────────

    def action_mark_done(self):
        for task in self:
            task.write({
                'state': 'done',
                'completed_date': fields.Date.today(),
                'completed_by': self.env.user.id,
            })
            task.message_post(
                body=_('✅ Task marked as Done by %s') % self.env.user.name
            )
        # Check if all tasks done → auto-complete plan
        for plan in self.mapped('onboarding_id'):
            if all(t.state in ('done', 'skipped') for t in plan.task_ids):
                plan.state = 'done'
                plan.message_post(body=_('🎉 All tasks completed — Onboarding auto-completed!'))

    def action_mark_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_skip(self):
        for task in self:
            if task.is_mandatory:
                raise UserError(
                    _('Cannot skip mandatory task: %s') % task.name
                )
            task.state = 'skipped'

    def action_reset_pending(self):
        self.write({
            'state': 'pending',
            'completed_date': False,
            'completed_by': False,
        })
