from odoo import models, fields, api

class EmployeeSalaryComponent(models.Model):
    _name = 'employee.salary.component'
    _description = 'Employee Salary Component'
    _order = 'sequence, id'

    contract_id = fields.Many2one('hr.contract', string='Contract', ondelete='cascade')
    name = fields.Char(string='Component Name', required=True)
    component_type = fields.Selection([
        ('earning', 'Earning'),
        ('deduction', 'Deduction')
    ], string='Component Type', required=True)
    
    calculation_method = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], string='Calculation Method', required=True)
    
    based_on = fields.Selection([
        ('gross_salary', 'Gross Salary'),
        ('basic_salary', 'Basic Salary'),
        ('hra', 'HRA'),
        ('travel_allowance', 'Travel Allowance'),
        ('medical_allowance', 'Medical Allowance'),
        ('other', 'Other Component')
    ], string='Calculation Base')
    
    based_on_component_id = fields.Many2one('employee.salary.component', string='Other Component')
    
    amount_or_percentage = fields.Float(string='Amount / Percentage', required=True)
    calculated_amount = fields.Float(string='Calculated Amount', compute='_compute_calculated_amount')
    sequence = fields.Integer(string='Sequence', default=10)

    @api.depends('amount_or_percentage', 'calculation_method', 'based_on', 'contract_id', 'contract_id.wage')
    def _compute_calculated_amount(self):
        # A lightweight non-recursive front-end estimation purely for HR visibility 
        for rec in self:
            if rec.calculation_method == 'fixed':
                rec.calculated_amount = rec.amount_or_percentage
            else:
                base = 0.0
                if rec.based_on == 'gross_salary':
                    base = rec.contract_id.wage if rec.contract_id else 0.0
                elif rec.based_on == 'basic_salary':
                    if rec.contract_id:
                        basic_comps = [c for c in rec.contract_id.employee_component_ids if c.name and 'basic' in c.name.lower()]
                        if basic_comps:
                            b_comp = basic_comps[0]
                            base = b_comp.amount_or_percentage if b_comp.calculation_method == 'fixed' else ((rec.contract_id.wage or 0.0) * b_comp.amount_or_percentage / 100.0)
                elif rec.based_on == 'hra':
                    if rec.contract_id:
                        hra_comps = [c for c in rec.contract_id.employee_component_ids if c.name and 'hra' in c.name.lower()]
                        if hra_comps:
                            h = hra_comps[0]
                            # we assume hra base is either gross or basic for this estimation
                            if h.calculation_method == 'fixed':
                                base = h.amount_or_percentage
                            else:
                                if h.based_on == 'basic_salary':
                                    basic_comps = [c for c in rec.contract_id.employee_component_ids if c.name and 'basic' in c.name.lower()]
                                    b_val = 0
                                    if basic_comps:
                                        bc = basic_comps[0]
                                        b_val = bc.amount_or_percentage if bc.calculation_method == 'fixed' else ((rec.contract_id.wage or 0.0) * bc.amount_or_percentage / 100.0)
                                    base = b_val * (h.amount_or_percentage / 100.0)
                                else:
                                    base = (rec.contract_id.wage or 0.0) * (h.amount_or_percentage / 100.0)
                rec.calculated_amount = base * (rec.amount_or_percentage / 100.0)
