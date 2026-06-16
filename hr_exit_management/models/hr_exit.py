# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrExit(models.Model):
    _name = 'hr.exit'
    _description = 'Employee Exit Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                        readonly=True, default=lambda self: _('New'))

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True,
        domain=[('active', '=', True)])
    department_id = fields.Many2one(
        related='employee_id.department_id', string='Department', store=True, readonly=True)
    job_id = fields.Many2one(
        related='employee_id.job_id', string='Job Position', store=True, readonly=True)
    manager_id = fields.Many2one(
        related='employee_id.parent_id', string='Manager', store=True, readonly=True)
    user_id = fields.Many2one(
        related='employee_id.user_id', string='Related User', store=True, readonly=True)

    resignation_date = fields.Date(string='Resignation Date', required=True,
                                    tracking=True, default=fields.Date.context_today)
    last_working_day = fields.Date(string='Last Working Day', required=True, tracking=True)
    notice_period_days = fields.Integer(string='Notice Period (Days)', compute='_compute_notice_period', store=True)
    required_notice_days = fields.Integer(string='Required Notice (Days)', default=30)
    notice_compliant = fields.Boolean(string='Notice Period Compliant',
                                       compute='_compute_notice_period', store=True)

    reason = fields.Text(string='Reason for Leaving', required=True)

    kt_plan = fields.Text(string='Knowledge Transfer Plan')
    kt_completed = fields.Boolean(string='Knowledge Transfer Completed')

    access_revoked = fields.Boolean(string='System Access Revoked')
    access_revocation_notes = fields.Text(string='Access Revocation Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager_accepted', 'Manager Accepted'),
        ('hr_accepted', 'HR Accepted'),
        ('clearance', 'Clearance In Progress'),
        ('fnf', 'F&F Settlement'),
        ('done', 'Done / Relieved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, group_expand='_expand_states')

    clearance_ids = fields.One2many('hr.exit.clearance', 'exit_id', string='Clearance Checklist')
    clearance_count = fields.Integer(compute='_compute_clearance_count')
    all_cleared = fields.Boolean(compute='_compute_all_cleared', string='All Cleared')

    fnf_id = fields.One2many('hr.exit.fnf', 'exit_id', string='F&F Settlement')
    interview_id = fields.One2many('hr.exit.interview', 'exit_id', string='Exit Interview')

    pending_assets = fields.Integer(string='Pending Assets', compute='_compute_pending_assets', search='_search_pending_assets')

    relieving_letter_issued = fields.Boolean(string='Relieving Letter Issued')
    relieving_letter_date = fields.Date(string='Relieving Letter Date')

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.exit') or _('New')
        return super().create(vals_list)

    @api.model
    def _expand_states(self, states, domain, order=None):
        return [key for key, val in type(self).state.selection]

    @api.depends('resignation_date', 'last_working_day', 'required_notice_days')
    def _compute_notice_period(self):
        for rec in self:
            if rec.resignation_date and rec.last_working_day:
                delta = (rec.last_working_day - rec.resignation_date).days
                rec.notice_period_days = delta
                rec.notice_compliant = delta >= rec.required_notice_days
            else:
                rec.notice_period_days = 0
                rec.notice_compliant = False

    @api.depends('clearance_ids')
    def _compute_clearance_count(self):
        for rec in self:
            rec.clearance_count = len(rec.clearance_ids)

    @api.depends('clearance_ids.status')
    def _compute_all_cleared(self):
        for rec in self:
            if rec.clearance_ids:
                rec.all_cleared = all(
                    line.status in ('cleared', 'na') for line in rec.clearance_ids
                )
            else:
                rec.all_cleared = False

    @api.depends('employee_id')
    def _compute_pending_assets(self):
        Asset = self.env.get('hr.asset')
        for rec in self:
            if Asset is not None and rec.employee_id:
                rec.pending_assets = Asset.search_count([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', 'not in', ['returned', 'cancelled']),
                ]) if 'state' in Asset._fields else 0
            else:
                rec.pending_assets = 0

    def _search_pending_assets(self, operator, value):
        Asset = self.env.get('hr.asset')
        if Asset is None or 'state' not in Asset._fields:
            if operator == '>' and value == 0:
                return [('id', '=', False)]
            return []
        
        assets = Asset.search([('state', 'not in', ['returned', 'cancelled'])])
        employee_ids = assets.mapped('employee_id').ids
        if operator == '>' and value == 0:
            return [('employee_id', 'in', employee_ids)]
        elif operator == '=' and value == 0:
            return [('employee_id', 'not in', employee_ids)]
        
        return [('employee_id', 'in', employee_ids)]

    @api.constrains('resignation_date', 'last_working_day')
    def _check_dates(self):
        for rec in self:
            if rec.last_working_day < rec.resignation_date:
                raise ValidationError(_('Last Working Day cannot be before Resignation Date.'))

    # -------------------------------------------------------------
    # Workflow Actions (state: Draft -> Manager Accepted -> HR Accepted
    #                          -> Clearance -> F&F -> Done)
    # -------------------------------------------------------------

    def action_submit(self):
        """Step 1: Employee submits resignation."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
        self.write({'state': 'draft'})
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_('Resignation submitted - awaiting Manager acceptance'),
            user_id=self.manager_id.user_id.id or self.env.uid)
        return True

    def action_manager_accept(self):
        """Step 2: Manager accepts resignation & triggers KT plan."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Resignation must be in Draft state.'))
            if not rec.kt_plan:
                rec.kt_plan = _('Knowledge transfer plan to be documented by %s and %s') % (
                    rec.employee_id.name, rec.manager_id.name or _('Manager'))
        self.write({'state': 'manager_accepted'})
        return True

    def action_hr_accept(self):
        """Step 3: HR acknowledges and confirms notice period compliance."""
        for rec in self:
            if rec.state != 'manager_accepted':
                raise UserError(_('Manager must accept before HR acknowledgement.'))
        self.write({'state': 'hr_accepted'})
        return True

    def action_start_clearance(self):
        """Step 4 & 5: Start Knowledge Transfer + Asset Return + Clearance checklist."""
        for rec in self:
            if rec.state != 'hr_accepted':
                raise UserError(_('HR must acknowledge before starting clearance.'))
            if not rec.clearance_ids:
                rec._generate_clearance_checklist()
        self.write({'state': 'clearance'})
        return True

    def _generate_clearance_checklist(self):
        """Auto-generate IT / Finance / Admin / HR clearance lines."""
        self.ensure_one()
        templates = self.env['hr.exit.clearance.template'].search([])
        if not templates:
            templates = self.env['hr.exit.clearance.template'].create([
                {'name': 'Email & ERP Access Revocation', 'department': 'it'},
                {'name': 'Laptop / Hardware Return', 'department': 'it'},
                {'name': 'GitHub / VPN Access Revocation', 'department': 'it'},
                {'name': 'Outstanding Advances / Loans Settlement', 'department': 'finance'},
                {'name': 'Expense Reimbursement Clearance', 'department': 'finance'},
                {'name': 'ID Card / Access Card Return', 'department': 'admin'},
                {'name': 'Company Assets (Furniture, Keys) Return', 'department': 'admin'},
                {'name': 'F&F Documentation Complete', 'department': 'hr'},
                {'name': 'Exit Interview Conducted', 'department': 'hr'},
            ])
        lines = []
        for tmpl in templates:
            lines.append((0, 0, {
                'department': tmpl.department,
                'item': tmpl.name,
                'status': 'pending',
            }))
        self.clearance_ids = lines

    def action_revoke_access(self):
        """Step 6: IT Team deactivates email, ERP, GitHub, VPN."""
        for rec in self:
            if rec.state != 'clearance':
                raise UserError(_('Access revocation only applies during Clearance stage.'))
        self.write({'access_revoked': True})
        return True

    def action_move_to_fnf(self):
        """Step 7: Move to F&F Settlement once clearance is complete."""
        for rec in self:
            if rec.state != 'clearance':
                raise UserError(_('Must be in Clearance stage to proceed to F&F.'))
            if not rec.all_cleared:
                raise UserError(_('All clearance items must be Cleared or N/A before proceeding to F&F.'))
            if rec.pending_assets > 0:
                raise UserError(_('Cannot proceed to F&F: %s pending asset(s) not yet returned.') % rec.pending_assets)
            if not rec.fnf_id:
                self.env['hr.exit.fnf'].create({'exit_id': rec.id})
        self.write({'state': 'fnf'})
        return True

    def action_complete_fnf(self):
        """Step 7 complete: F&F computed and confirmed by Payroll."""
        for rec in self:
            if rec.state != 'fnf':
                raise UserError(_('Must be in F&F Settlement stage.'))
            if not rec.fnf_id:
                raise UserError(_('F&F record not found. Please compute settlement first.'))
            for fnf in rec.fnf_id:
                fnf.action_confirm()
        return True

    def action_done(self):
        """Step 9 & 10: Issue relieving letter & archive employee."""
        for rec in self:
            if rec.state != 'fnf':
                raise UserError(_('F&F Settlement must be completed before relieving.'))
            if not rec.fnf_id or rec.fnf_id[0].state != 'confirmed':
                raise UserError(_('F&F Settlement must be confirmed before issuing relieving letter.'))
            if not rec.interview_id:
                raise UserError(_('Exit Interview must be logged before relieving the employee.'))
            rec.write({
                'state': 'done',
                'relieving_letter_issued': True,
                'relieving_letter_date': fields.Date.context_today(rec),
            })
            rec._action_archive_employee()
        return True

    def action_print_relieving_letter(self):
        self.ensure_one()
        return self.env.ref('hr_exit_management.action_report_relieving_letter').report_action(self)

    def action_cancel(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('Cannot cancel a completed exit.'))
        self.write({'state': 'cancelled'})
        return True

    def action_reset_draft(self):
        self.write({'state': 'draft'})
        return True

    def _action_archive_employee(self):
        """Step 10: Archive employee record in Odoo (not delete)."""
        self.ensure_one()
        if self.employee_id.active:
            self.employee_id.write({'active': False})
            if self.employee_id.user_id:
                self.employee_id.user_id.write({'active': False})
        return True

    def action_view_clearance(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'hr_exit_management.action_hr_exit_clearance')
        action['domain'] = [('exit_id', '=', self.id)]
        action['context'] = {'default_exit_id': self.id}
        return action
