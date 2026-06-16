# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrAppraisal(models.Model):
    _name = 'hr.appraisal'
    _description = 'Employee Appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_close desc, id desc'
    _rec_name = 'employee_id'

    # ------------------------------------------------------------------
    # Basic Info
    # ------------------------------------------------------------------
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        tracking=True, ondelete='cascade')
    department_id = fields.Many2one(
        related='employee_id.department_id', string='Department',
        store=True, readonly=True)
    job_id = fields.Many2one(
        related='employee_id.job_id', string='Job Position',
        store=True, readonly=True)

    manager_ids = fields.Many2many(
        'hr.employee', 'hr_appraisal_manager_rel', 'appraisal_id',
        'employee_id', string='Managers/Appraisers', tracking=True)

    appraisal_template_id = fields.Many2one(
        'hr.appraisal.template', string='Appraisal Template')

    date_open = fields.Date(
        string='Appraisal Start Date', default=fields.Date.context_today,
        required=True, tracking=True)
    date_close = fields.Date(
        string='Appraisal Deadline', required=True, tracking=True)

    state = fields.Selection([
        ('new', 'To Confirm'),
        ('pending', 'Confirmed'),
        ('manager_review', 'Manager Review'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='new', tracking=True, group_expand='_expand_states')

    company_id = fields.Many2one(
        'res.company', related='employee_id.company_id', store=True)

    # ------------------------------------------------------------------
    # Self Assessment
    # ------------------------------------------------------------------
    employee_feedback = fields.Html(string='Employee Self Assessment')
    employee_feedback_full = fields.Html(
        string='Employee Feedback (Full)',
        help='Detailed self-assessment: My Work, My Future, My Feelings')
    employee_feedback_date = fields.Date(string='Self Assessment Date')

    # ------------------------------------------------------------------
    # Manager Feedback
    # ------------------------------------------------------------------
    manager_feedback = fields.Html(string='Manager Feedback')
    manager_feedback_date = fields.Date(string='Manager Feedback Date')

    # ------------------------------------------------------------------
    # KRA / KPI
    # ------------------------------------------------------------------
    kra_ids = fields.One2many(
        'hr.appraisal.kra', 'appraisal_id', string='Key Result Areas')
    kpi_ids = fields.One2many(
        'hr.appraisal.kpi', 'appraisal_id', string='KPIs')

    total_weightage = fields.Float(
        string='Total KRA Weightage', compute='_compute_total_weightage',
        store=True, help='Sum of all KRA weightages, should equal 100')

    overall_rating = fields.Float(
        string='Overall Rating', compute='_compute_overall_rating',
        store=True, digits=(5, 2), tracking=True,
        help='Weighted average achievement % across all KRAs')

    bell_curve_rating = fields.Selection([
        ('far_below', 'Far Below Expectations'),
        ('below', 'Below Expectations'),
        ('meets', 'Meets Expectations'),
        ('exceeds', 'Exceeds Expectations'),
    ], string='Bell Curve Rating', tracking=True,
        help='Final rating bucket - manually assigned by HR based on overall rating and forced ranking')

    # ------------------------------------------------------------------
    # Skills Review
    # ------------------------------------------------------------------
    employee_skill_ids = fields.One2many(
        'hr.employee.skill', related='employee_id.employee_skill_ids',
        string='Employee Skills', readonly=False)

    # ------------------------------------------------------------------
    # 360 Feedback
    # ------------------------------------------------------------------
    feedback_ids = fields.One2many(
        'hr.appraisal.feedback', 'appraisal_id', string='360 Feedback')
    feedback_count = fields.Integer(
        string='Feedback Count', compute='_compute_feedback_count')

    # ------------------------------------------------------------------
    # Goal Carry Forward
    # ------------------------------------------------------------------
    carry_to_next_cycle = fields.Boolean(
        string='Carry Forward Open Goals',
        help='If checked, incomplete KRAs/KPIs will be copied to the next appraisal cycle')
    next_appraisal_id = fields.Many2one(
        'hr.appraisal', string='Next Cycle Appraisal', copy=False, readonly=True)
    previous_appraisal_id = fields.Many2one(
        'hr.appraisal', string='Previous Cycle Appraisal', copy=False, readonly=True)

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('kra_ids.weightage')
    def _compute_total_weightage(self):
        for record in self:
            record.total_weightage = sum(record.kra_ids.mapped('weightage'))

    @api.depends('kra_ids.weightage', 'kra_ids.kpi_ids.achievement_pct')
    def _compute_overall_rating(self):
        for record in self:
            total = 0.0
            for kra in record.kra_ids:
                kpis = kra.kpi_ids
                if kpis:
                    avg_achievement = sum(kpis.mapped('achievement_pct')) / len(kpis)
                else:
                    avg_achievement = 0.0
                total += avg_achievement * (kra.weightage / 100.0)
            record.overall_rating = total

    def _compute_feedback_count(self):
        for record in self:
            record.feedback_count = len(record.feedback_ids)

    @api.model
    def _expand_states(self, states, domain, order=None):
        return [key for key, val in self._fields['state'].selection]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('kra_ids')
    def _check_kra_weightage(self):
        for record in self:
            if record.kra_ids and record.state in ('pending', 'done'):
                total = sum(record.kra_ids.mapped('weightage'))
                if round(total, 2) != 100.0:
                    raise ValidationError(
                        "Total KRA weightage must equal 100%% (currently %.2f%%) "
                        "before confirming the appraisal." % total)

    # ------------------------------------------------------------------
    # Actions / Workflow
    # ------------------------------------------------------------------
    def action_confirm(self):
        self._check_kra_weightage()
        self.write({'state': 'pending'})

    def action_manager_review(self):
        self.write({'state': 'manager_review'})

    def action_done(self):
        for record in self:
            if not record.bell_curve_rating:
                raise ValidationError("Please assign a Bell Curve Rating before closing the appraisal.")
        self.write({'state': 'done'})
        self._update_employee_skills()
        for record in self:
            if record.carry_to_next_cycle:
                record._action_carry_forward_goals()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'new'})

    def action_set_employee_feedback_today(self):
        self.write({'employee_feedback_date': fields.Date.context_today(self)})

    def action_set_manager_feedback_today(self):
        self.write({'manager_feedback_date': fields.Date.context_today(self)})

    # ------------------------------------------------------------------
    # Skills Integration
    # ------------------------------------------------------------------
    def _update_employee_skills(self):
        """ Push updated skill levels (entered on the appraisal) back to
        the employee's profile - 'Integration with Skills' requirement. """
        for record in self:
            for skill_line in record.employee_skill_ids:
                skill_line.employee_id = record.employee_id.id

    # ------------------------------------------------------------------
    # Goal Carry Forward
    # ------------------------------------------------------------------
    def _action_carry_forward_goals(self):
        self.ensure_one()
        next_date_open = self.date_close
        next_date_close = fields.Date.add(next_date_open, months=6)

        new_appraisal = self.copy({
            'employee_id': self.employee_id.id,
            'manager_ids': [(6, 0, self.manager_ids.ids)],
            'appraisal_template_id': self.appraisal_template_id.id,
            'date_open': next_date_open,
            'date_close': next_date_close,
            'state': 'new',
            'employee_feedback': False,
            'employee_feedback_full': False,
            'manager_feedback': False,
            'employee_feedback_date': False,
            'manager_feedback_date': False,
            'bell_curve_rating': False,
            'overall_rating': 0.0,
            'previous_appraisal_id': self.id,
            'next_appraisal_id': False,
            'carry_to_next_cycle': False,
            'kra_ids': [],
            'kpi_ids': [],
            'feedback_ids': [],
        })

        for kra in self.kra_ids:
            open_kpis = kra.kpi_ids.filtered(lambda k: k.achievement_pct < 100.0)
            if not open_kpis:
                continue
            new_kra = self.env['hr.appraisal.kra'].create({
                'appraisal_id': new_appraisal.id,
                'name': kra.name,
                'weightage': kra.weightage,
                'description': kra.description,
            })
            for kpi in open_kpis:
                self.env['hr.appraisal.kpi'].create({
                    'appraisal_id': new_appraisal.id,
                    'kra_id': new_kra.id,
                    'kpi_name': kpi.kpi_name,
                    'target_value': kpi.target_value,
                    'actual_value': 0.0,
                    'uom': kpi.uom,
                    'carry_to_next_cycle': True,
                    'from_kpi_id': kpi.id,
                })

        self.next_appraisal_id = new_appraisal.id
        return new_appraisal

    def action_open_next_appraisal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Next Cycle Appraisal',
            'res_model': 'hr.appraisal',
            'view_mode': 'form',
            'res_id': self.next_appraisal_id.id,
        }
