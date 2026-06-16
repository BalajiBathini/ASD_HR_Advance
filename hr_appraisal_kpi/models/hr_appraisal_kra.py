# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrAppraisalKra(models.Model):
    _name = 'hr.appraisal.kra'
    _description = 'Appraisal Key Result Area'
    _order = 'sequence, id'

    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)

    name = fields.Char(string='KRA Description', required=True,
                        help='Key Result Area description')
    weightage = fields.Float(
        string='Weightage (%)', required=True, default=0.0,
        help='Weight % per KRA (sum of all KRAs for an appraisal should equal 100)')
    description = fields.Text(string='Additional Notes')

    kpi_ids = fields.One2many(
        'hr.appraisal.kpi', 'kra_id', string='KPIs')
    kpi_count = fields.Integer(string='KPI Count', compute='_compute_kpi_count')

    achievement_pct = fields.Float(
        string='KRA Achievement (%)', compute='_compute_achievement_pct',
        digits=(5, 2), store=True,
        help='Average achievement % across all KPIs under this KRA')

    employee_id = fields.Many2one(
        related='appraisal_id.employee_id', string='Employee', store=True)

    @api.depends('kpi_ids')
    def _compute_kpi_count(self):
        for record in self:
            record.kpi_count = len(record.kpi_ids)

    @api.depends('kpi_ids.achievement_pct')
    def _compute_achievement_pct(self):
        for record in self:
            kpis = record.kpi_ids
            if kpis:
                record.achievement_pct = sum(kpis.mapped('achievement_pct')) / len(kpis)
            else:
                record.achievement_pct = 0.0

    @api.constrains('weightage')
    def _check_weightage_range(self):
        for record in self:
            if record.weightage < 0 or record.weightage > 100:
                raise ValidationError("KRA weightage must be between 0 and 100.")
