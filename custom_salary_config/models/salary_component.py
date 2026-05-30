from odoo import models, fields, api

class SalaryComponent(models.Model):
    _name = 'salary.component'
    _description = 'Salary Component Configuration'
    _order = 'sequence, id'

    name = fields.Char(string='Component Name', required=True)
    structure_id = fields.Many2one('hr.payroll.structure', string='Salary Structure', ondelete='cascade')
    rule_id = fields.Many2one('hr.salary.rule', string='Linked Salary Rule', readonly=True, ondelete='cascade')
    
    component_type = fields.Selection([
        ('earning', 'Earning'),
        ('deduction', 'Deduction')
    ], string='Component Type', required=True, default='earning')
    
    calculation_method = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], string='Calculation Method', required=True, default='fixed')
    
    based_on = fields.Selection([
        ('gross_salary', 'Gross Salary (Wage)'),
        ('basic_salary', 'Basic Salary'),
        ('hra', 'HRA'),
        ('other', 'Other Rules')
    ], string='Calculation Base', default='gross_salary')
    
    based_on_rule_id = fields.Many2one('hr.salary.rule', string='Based On Rule')
    
    amount = fields.Float(string='Amount / Percentage', required=True, default=0.0)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        components = super().create(vals_list)
        components._sync_to_salary_rule()
        return components

    def write(self, vals):
        res = super().write(vals)
        self._sync_to_salary_rule()
        return res

    def unlink(self):
        rules = self.mapped('rule_id')
        res = super().unlink()
        rules.unlink()
        return res

    def _sync_to_salary_rule(self):
        for comp in self:
            code = ''.join(e for e in comp.name.upper() if e.isalnum()) + '_' + str(comp.id)
            
            category_ext_id = 'payroll.BASIC' if comp.component_type == 'earning' else 'payroll.DED'
            category = self.env.ref(category_ext_id, raise_if_not_found=False)
            
            rule_vals = {
                'name': comp.name,
                'code': code[:32],
                'sequence': comp.sequence,
                'category_id': category.id if category else False,
                'amount_select': 'code',
                'amount_python_compute': comp._generate_python_compute(),
            }
            
            if comp.rule_id:
                comp.rule_id.write(rule_vals)
            else:
                new_rule = self.env['hr.salary.rule'].create(rule_vals)
                comp.write({'rule_id': new_rule.id})
                
            # Ensure the rule is attached to the structure
            if comp.structure_id and comp.rule_id not in comp.structure_id.rule_ids:
                comp.structure_id.rule_ids = [(4, comp.rule_id.id)]

    def _generate_python_compute(self):
        lines = []
        lines.append(f"emp_comp = contract.employee_component_ids.filtered(lambda c: c.name == '{self.name}' and c.component_type == '{self.component_type}')")
        lines.append("if emp_comp:")
        lines.append("    active_val = emp_comp[0].amount_or_percentage")
        lines.append("    calc_method = emp_comp[0].calculation_method")
        lines.append("else:")
        lines.append(f"    active_val = {self.amount}")
        lines.append(f"    calc_method = '{self.calculation_method}'")
        
        lines.append("if calc_method == 'fixed':")
        lines.append("    result_val = active_val")
        lines.append("elif calc_method == 'percentage':")
        
        if self.based_on == 'gross_salary':
            lines.append("    base_amount = contract.wage")
        elif self.based_on == 'basic_salary':
            # Usually basic salary code is BASIC. We can access categories.BASIC safely
            lines.append("    base_amount = categories.BASIC if 'BASIC' in categories.dict else contract.wage")
        elif self.based_on == 'hra':
            lines.append("    base_amount = categories.HRA if 'HRA' in categories.dict else 0.0")
        elif self.based_on == 'other' and self.based_on_rule_id:
            # For specific rule dependency
            code = self.based_on_rule_id.code
            lines.append(f"    base_amount = rules.dict.get('{code}', 0.0).total if '{code}' in rules.dict else 0.0")
        else:
            lines.append("    base_amount = contract.wage")
            
        lines.append("    result_val = base_amount * (active_val / 100.0)")
        
        lines.append("result = result_val")
        return "\n".join(lines)
