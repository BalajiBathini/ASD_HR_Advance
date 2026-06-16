# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    appraisal_ids = fields.One2many(
        'hr.appraisal', 'employee_id', string='Appraisals')
    appraisal_count = fields.Integer(
        string='Appraisal Count', compute='_compute_appraisal_count')

    last_appraisal_id = fields.Many2one(
        'hr.appraisal', string='Last Appraisal',
        compute='_compute_last_appraisal_id', store=True)
    last_appraisal_rating = fields.Float(
        related='last_appraisal_id.overall_rating', string='Last Overall Rating')
    last_bell_curve_rating = fields.Selection(
        related='last_appraisal_id.bell_curve_rating', string='Last Bell Curve Rating')

    def _compute_appraisal_count(self):
        for employee in self:
            employee.appraisal_count = len(employee.appraisal_ids)

    @api.depends('appraisal_ids.state', 'appraisal_ids.date_close')
    def _compute_last_appraisal_id(self):
        for employee in self:
            appraisals = employee.appraisal_ids.filtered(lambda a: a.state == 'done')
            employee.last_appraisal_id = appraisals[:1].id if appraisals else False

    def action_open_appraisals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appraisals',
            'res_model': 'hr.appraisal',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
