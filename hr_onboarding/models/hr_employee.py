from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    onboarding_id = fields.One2many(
        'hr.onboarding',
        'employee_id',
        string='Onboarding Plans',
    )
    onboarding_count = fields.Integer(
        string='Onboarding Plans',
        compute='_compute_onboarding_count',
    )
    onboarding_state = fields.Selection(
        selection=[
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('done', 'Completed'),
        ],
        string='Onboarding Status',
        compute='_compute_onboarding_state',
        store=True,
    )

    @api.depends('onboarding_id')
    def _compute_onboarding_count(self):
        for emp in self:
            emp.onboarding_count = len(emp.onboarding_id)

    @api.depends('onboarding_id.state')
    def _compute_onboarding_state(self):
        for emp in self:
            plans = emp.onboarding_id
            if not plans:
                emp.onboarding_state = 'not_started'
            elif any(p.state == 'done' for p in plans):
                emp.onboarding_state = 'done'
            elif any(p.state == 'in_progress' for p in plans):
                emp.onboarding_state = 'in_progress'
            else:
                emp.onboarding_state = 'not_started'

    def action_view_onboarding(self):
        self.ensure_one()
        return {
            'name': _('Onboarding — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.onboarding',
            'view_mode': 'list,form,kanban',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'default_join_date': self.joining_date,
            },
        }

    def action_create_onboarding(self):
        """Quick action: open create onboarding wizard from employee form."""
        self.ensure_one()
        default_template = self.env['hr.onboarding.template'].search(
            [('active', '=', True)], limit=1
        )
        return {
            'name': _('Create Onboarding Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.onboarding',
            'view_mode': 'form',
            'context': {
                'default_employee_id': self.id,
                'default_join_date': self.joining_date or fields.Date.today(),
                'default_template_id': default_template.id if default_template else False,
            },
            'target': 'new',
        }
