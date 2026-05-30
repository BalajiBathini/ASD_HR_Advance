from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    gross_salary = fields.Monetary(string='Monthly Wage / Gross Salary', related='wage', store=True, tracking=True)
    annual_ctc = fields.Monetary(string='Annual CTC', compute='_compute_annual_ctc', store=True)
    
    employee_component_ids = fields.One2many('employee.salary.component', 'contract_id', string='Employee Salary Components')
    
    total_earnings = fields.Monetary(string='Total Earnings', compute='_compute_totals')
    total_deductions = fields.Monetary(string='Total Deductions', compute='_compute_totals')
    net_salary = fields.Monetary(string='Net Salary', compute='_compute_totals')
    
    is_structure_editable = fields.Boolean(string='Is Structure Editable', default=False)

    @api.depends('gross_salary')
    def _compute_annual_ctc(self):
        for rec in self:
            rec.annual_ctc = rec.gross_salary * 12

    @api.depends('employee_component_ids.calculated_amount', 'employee_component_ids.component_type')
    def _compute_totals(self):
        for rec in self:
            earnings = sum(comp.calculated_amount for comp in rec.employee_component_ids if comp.component_type == 'earning')
            deductions = sum(comp.calculated_amount for comp in rec.employee_component_ids if comp.component_type == 'deduction')
            rec.total_earnings = earnings
            rec.total_deductions = deductions
            rec.net_salary = earnings - deductions

    @api.constrains('employee_component_ids', 'wage')
    def _check_total_earnings(self):
        for rec in self:
            if rec.total_earnings > rec.gross_salary:
                has_bonus = any(comp.component_type == 'earning' and 'bonus' in comp.name.lower() for comp in rec.employee_component_ids)
                if not has_bonus:
                    raise ValidationError(_("Total Earnings (₹ %(earnings)s) cannot exceed the Monthly Wage (₹ %(wage)s) unless a Bonus component is explicitly defined in the structure.") % {
                        'earnings': rec.total_earnings,
                        'wage': rec.gross_salary
                    })

# End compute ct

    def action_load_structure(self):
        for rec in self:
            if not rec.struct_id:
                continue
            
            # Remove existing
            rec.employee_component_ids.unlink()
            
            # Map original components to new ones
            id_mapping = {}
            
            for comp in rec.struct_id.custom_component_ids:
                vals = {
                    'name': comp.name,
                    'component_type': comp.component_type,
                    'calculation_method': comp.calculation_method,
                    'based_on': comp.based_on,
                    'amount_or_percentage': comp.amount,
                    'sequence': comp.sequence,
                    'contract_id': rec.id,
                }
                new_comp = self.env['employee.salary.component'].create(vals)
                id_mapping[comp.id] = new_comp.id
                

    def action_edit_structure(self):
        for rec in self:
            rec.is_structure_editable = True

    def action_save_structure(self):
        for rec in self:
            rec.is_structure_editable = False
            # Recalculations are handled by compute fields
            
    def action_recalculate(self):
        pass
