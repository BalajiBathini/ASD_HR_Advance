from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Running'),
        ('close', 'Expired'),
        ('cancel', 'Relieve')
    ], string='Status', tracking=True, help='Status of the contract', default='draft')

    annual_ctc = fields.Monetary(string='Annual CTC', compute='_compute_annual_ctc', inverse='_inverse_annual_ctc', store=True)


    employee_component_ids = fields.One2many('employee.salary.component', 'contract_id', string='Employee Salary Components')
    revision_ids = fields.One2many('hr.contract.structure.revision', 'contract_id', string='Revisions')
    
    total_earnings = fields.Monetary(string='Total Earnings', compute='_compute_totals')
    total_deductions = fields.Monetary(string='Total Deductions', compute='_compute_totals')
    net_salary = fields.Monetary(string='Net Salary', compute='_compute_totals')
    
    revision_indicator_html = fields.Html(string='Revision Indicator', compute='_compute_revision_indicator')
    salary_status = fields.Selection([
        ('approved', 'Approved'),
        ('editing', 'Editing Structure'),
        ('pending', 'Pending Manager Approval')
    ], string='Salary Status', default='approved', tracking=True)
    is_structure_editable = fields.Boolean(string='Is Structure Editable', compute='_compute_is_structure_editable')
    
    @api.depends('salary_status')
    def _compute_is_structure_editable(self):
        for rec in self:
            rec.is_structure_editable = (rec.salary_status == 'editing')

    state_salary_policy_id = fields.Many2one(
        'hr.state.salary.policy', 
        string='State Salary Policy',
        compute='_compute_state_salary_policy_id',
        store=True,
        readonly=False
    )

    @api.depends('revision_ids.revision_type', 'revision_ids.percentage_change')
    def _compute_revision_indicator(self):
        for rec in self:
            html = False
            if rec.revision_ids:
                latest = rec.revision_ids[0]
                if latest.revision_type == 'increase':
                    tooltip = f"Previous CTC: \u20B9{int(latest.previous_ctc):,}&#10;Current CTC: \u20B9{int(latest.current_ctc):,}&#10;Increase Amount: \u20B9{int(latest.amount_change):,}"
                    html = f'<span class="text-success" style="cursor:help;" title="{tooltip}">&#8593; {latest.percentage_change:.2f}% Increased</span>'
                elif latest.revision_type == 'decrease':
                    tooltip = f"Previous CTC: \u20B9{int(latest.previous_ctc):,}&#10;Current CTC: \u20B9{int(latest.current_ctc):,}&#10;Decrease Amount: \u20B9{int(latest.amount_change):,}"
                    html = f'<span class="text-danger" style="cursor:help;" title="{tooltip}">&#8595; {latest.percentage_change:.2f}% Decreased</span>'
            rec.revision_indicator_html = html

    @api.depends('company_id', 'employee_id')
    def _compute_state_salary_policy_id(self):
        for rec in self:
            if not rec.company_id:
                continue
            
            # Try to match company and employee state
            employee_state = False
            if rec.employee_id:
                employee_state = rec.employee_id.private_state_id or (rec.employee_id.address_id and rec.employee_id.address_id.state_id)
            
            domain = [('company_id', '=', rec.company_id.id)]
            if employee_state:
                domain.append(('state_id', '=', employee_state.id))
            
            policy = self.env['hr.state.salary.policy'].search(domain, limit=1)
            
            # Fallback to the first policy for the company if no exact state match
            if not policy:
                policy = self.env['hr.state.salary.policy'].search([('company_id', '=', rec.company_id.id)], limit=1)
            
            if policy:
                rec.state_salary_policy_id = policy.id

    @api.constrains('annual_ctc', 'state_salary_policy_id')
    def _check_minimum_ctc(self):
        for rec in self:
            if rec.state_salary_policy_id and rec.annual_ctc < rec.state_salary_policy_id.min_ctc:
                raise ValidationError(_("The Annual CTC (₹ %(ctc)s) cannot be lower than the minimum wage (₹ %(min_wage)s) defined in the selected State Salary Policy.") % {
                    'ctc': rec.annual_ctc,
                    'min_wage': rec.state_salary_policy_id.min_ctc
                })
    @api.depends('wage')
    def _compute_annual_ctc(self):
        for rec in self:
            rec.annual_ctc = rec.wage * 12

    def _inverse_annual_ctc(self):
        for rec in self:
            rec.wage = rec.annual_ctc / 12.0

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
            if rec.total_earnings > rec.wage:
                has_bonus = any(comp.component_type == 'earning' and 'bonus' in comp.name.lower() for comp in rec.employee_component_ids)
                if not has_bonus:
                    raise ValidationError(_("Total Earnings (₹ %(earnings)s) cannot exceed the Monthly Wage (₹ %(wage)s) unless a Bonus component is explicitly defined in the structure.") % {
                        'earnings': rec.total_earnings,
                        'wage': rec.wage
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
            return {
                'name': _('Edit Structure Reason'),
                'type': 'ir.actions.act_window',
                'res_model': 'hr.contract.structure.edit.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_contract_id': rec.id,
                }
            }

    def action_save_structure(self):
        for rec in self:
            revisions = rec.revision_ids
            if revisions:
                latest_revision = revisions[0] # The one that was just created by 'Edit Structure'
                # Check for decrease
                if rec.annual_ctc < latest_revision.previous_ctc:
                    amount_change = latest_revision.previous_ctc - rec.annual_ctc
                    percentage_change = (amount_change / latest_revision.previous_ctc * 100.0) if latest_revision.previous_ctc else 0.0
                    return {
                        'name': _('Confirm Salary Decrease'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'hr.contract.salary.decrease.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_contract_id': rec.id,
                            'default_previous_ctc': latest_revision.previous_ctc,
                            'default_current_ctc': rec.annual_ctc,
                            'default_amount_change': amount_change,
                            'default_percentage_change': round(percentage_change, 2),
                        }
                    }
                else:
                    # It's an increase or unchanged
                    latest_revision.current_ctc = rec.annual_ctc
                    amount_change = rec.annual_ctc - latest_revision.previous_ctc
                    percentage_change = (amount_change / latest_revision.previous_ctc * 100.0) if latest_revision.previous_ctc else 0.0
                    latest_revision.amount_change = amount_change
                    latest_revision.percentage_change = round(percentage_change, 2)
                    
                    if rec.annual_ctc > latest_revision.previous_ctc:
                        latest_revision.revision_type = 'increase'
                        comment = "\nSalary revised from \u20B9{:,} to \u20B9{:,}.\nCTC increased by \u20B9{:,} ({:.2f}% increase).".format(
                            int(latest_revision.previous_ctc), int(rec.annual_ctc), int(amount_change), percentage_change
                        )
                        latest_revision.reason = (latest_revision.reason or '') + comment
                    else:
                        latest_revision.revision_type = 'unchanged'

            rec.salary_status = 'pending'
            # Recalculations are handled by compute fields
            
    def action_recalculate(self):
        pass

    def action_approve_salary(self):
        for rec in self:
            if rec.salary_status == 'pending':
                rec.salary_status = 'approved'

    def action_reject_salary(self):
        for rec in self:
            if rec.salary_status == 'pending':
                rec.salary_status = 'editing'

    def action_percentage_increase(self):
        for rec in self:
            return {
                'name': _('Percentage Increase'),
                'type': 'ir.actions.act_window',
                'res_model': 'hr.contract.percentage.increase.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_contract_id': rec.id,
                }
            }
