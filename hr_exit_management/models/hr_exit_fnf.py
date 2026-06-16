# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExitFnf(models.Model):
    _name = 'hr.exit.fnf'
    _description = 'Full & Final Settlement'

    exit_id = fields.Many2one('hr.exit', string='Exit Request', required=True, ondelete='cascade')
    employee_id = fields.Many2one(related='exit_id.employee_id', string='Employee', store=True)

    # Earnings
    pending_salary_days = fields.Integer(string='Pending Salary Days')
    per_day_salary = fields.Float(string='Per Day Salary')
    pending_salary = fields.Float(string='Pending Salary', compute='_compute_amounts', store=True)

    el_encashment_days = fields.Float(string='Earned Leave Days')
    el_encashment = fields.Float(string='Earned Leave Encashment', compute='_compute_amounts', store=True)

    gratuity_eligible = fields.Boolean(string='Gratuity Eligible')
    last_drawn_basic = fields.Float(string='Last Drawn Basic Salary')
    years_of_service = fields.Float(string='Years of Service')
    gratuity = fields.Float(string='Gratuity Payable', compute='_compute_amounts', store=True)

    bonus_arrears = fields.Float(string='Bonus / Arrears Payable')

    # Deductions
    notice_deduction_days = fields.Integer(string='Notice Shortfall Days')
    notice_deduction = fields.Float(string='Notice Period Deduction', compute='_compute_amounts', store=True)

    loan_advance_deduction = fields.Float(string='Loan / Advance Deduction')
    other_deductions = fields.Float(string='Other Deductions')

    # Totals
    total_earnings = fields.Float(string='Total Earnings', compute='_compute_amounts', store=True)
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_amounts', store=True)
    net_payable = fields.Float(string='Net Payable', compute='_compute_amounts', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft')

    notes = fields.Text(string='Notes')

    @api.depends('pending_salary_days', 'per_day_salary', 'el_encashment_days',
                  'gratuity_eligible', 'last_drawn_basic', 'years_of_service',
                  'bonus_arrears', 'notice_deduction_days', 'loan_advance_deduction',
                  'other_deductions')
    def _compute_amounts(self):
        for rec in self:
            # Earnings
            rec.pending_salary = rec.pending_salary_days * rec.per_day_salary
            rec.el_encashment = rec.el_encashment_days * rec.per_day_salary

            if rec.gratuity_eligible and rec.years_of_service >= 5:
                # Standard gratuity formula: (15/26) * last drawn basic * years of service
                rec.gratuity = (15 / 26) * rec.last_drawn_basic * rec.years_of_service
            else:
                rec.gratuity = 0.0

            rec.total_earnings = (
                rec.pending_salary + rec.el_encashment + rec.gratuity + rec.bonus_arrears
            )

            # Deductions
            rec.notice_deduction = rec.notice_deduction_days * rec.per_day_salary

            rec.total_deductions = (
                rec.notice_deduction + rec.loan_advance_deduction + rec.other_deductions
            )

            rec.net_payable = rec.total_earnings - rec.total_deductions

    def action_confirm(self):
        for rec in self:
            if rec.state == 'confirmed':
                raise UserError(_('F&F Settlement already confirmed.'))
            rec.state = 'confirmed'
        return True

    def action_reset_draft(self):
        self.write({'state': 'draft'})
