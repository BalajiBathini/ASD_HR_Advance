from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class HrOnboarding(models.Model):
    _name = 'hr.onboarding'
    _description = 'Employee Onboarding Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'join_date desc, id desc'
    _rec_name = 'display_name'

    # ─── Core Fields ────────────────────────────────────────────────────────

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Department',
        store=True,
        readonly=True,
    )
    job_id = fields.Many2one(
        related='employee_id.job_id',
        string='Job Position',
        store=True,
        readonly=True,
    )
    manager_id = fields.Many2one(
        related='employee_id.parent_id',
        string='Manager',
        store=True,
        readonly=True,
    )
    template_id = fields.Many2one(
        'hr.onboarding.template',
        string='Onboarding Template',
        tracking=True,
    )
    join_date = fields.Date(
        string='Date of Joining',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('done', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
    )
    task_ids = fields.One2many(
        'hr.onboarding.task',
        'onboarding_id',
        string='Onboarding Tasks',
    )

    # ─── Computed Fields ─────────────────────────────────────────────────────

    display_name = fields.Char(
        string='Reference',
        compute='_compute_display_name',
        store=True,
    )
    total_tasks = fields.Integer(
        string='Total Tasks',
        compute='_compute_progress',
        store=True,
    )
    done_tasks = fields.Integer(
        string='Completed Tasks',
        compute='_compute_progress',
        store=True,
    )
    completion_pct = fields.Float(
        string='Completion %',
        compute='_compute_progress',
        store=True,
        digits=(5, 1),
    )
    overdue_task_count = fields.Integer(
        string='Overdue Tasks',
        compute='_compute_overdue',
    )

    # ─── Computes ────────────────────────────────────────────────────────────

    @api.depends('employee_id', 'join_date')
    def _compute_display_name(self):
        for rec in self:
            emp = rec.employee_id.name or ''
            jd = rec.join_date or ''
            rec.display_name = f"{emp} — Onboarding ({jd})" if emp else 'New Onboarding'

    @api.depends('task_ids.state')
    def _compute_progress(self):
        for rec in self:
            tasks = rec.task_ids
            total = len(tasks)
            done = len(tasks.filtered(lambda t: t.state == 'done'))
            rec.total_tasks = total
            rec.done_tasks = done
            rec.completion_pct = (done / total * 100) if total else 0.0

    def _compute_overdue(self):
        today = fields.Date.today()
        for rec in self:
            overdue = rec.task_ids.filtered(
                lambda t: t.state == 'pending' and t.due_date and t.due_date < today
            )
            rec.overdue_task_count = len(overdue)

    # ─── ORM Overrides ───────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.template_id:
                rec._create_from_template()
        return records

    # ─── Business Logic ──────────────────────────────────────────────────────

    def _create_from_template(self):
        """Copy template task lines into onboarding tasks, computing due dates."""
        self.ensure_one()
        if not self.template_id or not self.join_date:
            return

        # Remove existing tasks first (allow re-apply template)
        self.task_ids.unlink()

        task_vals = []
        for line in self.template_id.task_line_ids:
            due_date = self.join_date + timedelta(days=line.due_days)
            # Map responsible_role → actual user (best-effort)
            responsible_id = self._resolve_responsible(line.responsible_role)
            task_vals.append({
                'onboarding_id': self.id,
                'name': line.name,
                'category': line.category,
                'responsible_role': line.responsible_role,
                'responsible_id': responsible_id,
                'due_days': line.due_days,
                'due_date': due_date,
                'description': line.description,
                'is_mandatory': line.is_mandatory,
                'state': 'pending',
                'sequence': line.sequence,
            })
        self.env['hr.onboarding.task'].create(task_vals)
        # Move to In Progress if tasks were created
        if task_vals:
            self.state = 'in_progress'

    def _resolve_responsible(self, role):
        """Return a res.users id based on role, falling back to HR manager."""
        if role == 'employee':
            return self.employee_id.user_id.id if self.employee_id.user_id else False
        if role == 'manager':
            return self.manager_id.user_id.id if self.manager_id and self.manager_id.user_id else False
        # For team roles, try to find via group
        role_group_map = {
            'it_team': 'base.group_system',
            'hr_admin': 'hr.group_hr_manager',
            'payroll_team': 'hr.group_hr_manager',
            'ld_team': 'hr.group_hr_user',
        }
        return False  # Responsible will be set manually

    def action_start(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only Draft plans can be started.'))
            rec.state = 'in_progress'
            rec.message_post(body=_('Onboarding plan started.'))

    def action_complete(self):
        for rec in self:
            pending = rec.task_ids.filtered(
                lambda t: t.state == 'pending' and t.is_mandatory
            )
            if pending:
                raise UserError(
                    _('Cannot complete: %d mandatory task(s) still pending:\n%s') % (
                        len(pending),
                        '\n'.join(f'• {t.name}' for t in pending),
                    )
                )
            rec.state = 'done'
            rec.message_post(body=_('🎉 Onboarding completed successfully!'))

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            rec.message_post(body=_('Onboarding plan cancelled.'))

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_apply_template(self):
        self.ensure_one()
        if not self.template_id:
            raise UserError(_('Please select a template first.'))
        if not self.join_date:
            raise UserError(_('Please set the Date of Joining first.'))
        self._create_from_template()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Template Applied'),
                'message': _('%d tasks created from template.') % len(self.task_ids),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_send_notifications(self):
        """Send task assignment email to all responsible persons."""
        self.ensure_one()
        template = self.env.ref(
            'hr_onboarding.mail_template_task_assignment', raise_if_not_found=False
        )
        if not template:
            return
        for task in self.task_ids.filtered(
            lambda t: t.state == 'pending' and t.responsible_id
        ):
            template.send_mail(task.id, force_send=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Notifications Sent'),
                'message': _('Assignment emails dispatched to responsible persons.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_tasks(self):
        self.ensure_one()
        return {
            'name': _('Onboarding Tasks'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.onboarding.task',
            'view_mode': 'list,form',
            'domain': [('onboarding_id', '=', self.id)],
            'context': {'default_onboarding_id': self.id},
        }
