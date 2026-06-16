# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrAppraisalKpi(models.Model):
    _name = 'hr.appraisal.kpi'
    _description = 'Appraisal KPI (Key Performance Indicator)'
    _order = 'sequence, id'

    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade')
    kra_id = fields.Many2one(
        'hr.appraisal.kra', string='Related KRA', ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)

    kpi_name = fields.Char(string='KPI Name', required=True,
                            help='Quantitative KPI description')
    uom = fields.Char(string='Unit of Measure', default='%',
                       help='e.g. %, Units, Calls, Hours, INR')

    target_value = fields.Float(
        string='Target Value', required=True, default=0.0,
        help='KPI target set at start of period')
    actual_value = fields.Float(
        string='Actual Value', default=0.0,
        help='Actual achievement at end of period')

    achievement_pct = fields.Float(
        string='Achievement (%)', compute='_compute_achievement_pct',
        store=True, digits=(5, 2),
        help='Computed: (actual / target) * 100')

    bell_curve_rating = fields.Selection([
        ('far_below', 'Far Below Expectations'),
        ('below', 'Below Expectations'),
        ('meets', 'Meets Expectations'),
        ('exceeds', 'Exceeds Expectations'),
    ], string='KPI Rating', compute='_compute_bell_curve_rating', store=True)

    employee_id = fields.Many2one(
        related='appraisal_id.employee_id', string='Employee', store=True)

    # Goal carry forward tracking
    carry_to_next_cycle = fields.Boolean(
        string='Carried Forward', default=False, copy=False,
        help='Indicates this KPI was carried forward from a previous appraisal cycle')
    from_kpi_id = fields.Many2one(
        'hr.appraisal.kpi', string='Source KPI (Previous Cycle)',
        copy=False, readonly=True)

    @api.depends('target_value', 'actual_value')
    def _compute_achievement_pct(self):
        for record in self:
            if record.target_value:
                record.achievement_pct = (record.actual_value / record.target_value) * 100.0
            else:
                record.achievement_pct = 0.0

    @api.depends('achievement_pct')
    def _compute_bell_curve_rating(self):
        for record in self:
            pct = record.achievement_pct
            if pct >= 110:
                record.bell_curve_rating = 'exceeds'
            elif pct >= 90:
                record.bell_curve_rating = 'meets'
            elif pct >= 60:
                record.bell_curve_rating = 'below'
            else:
                record.bell_curve_rating = 'far_below'
