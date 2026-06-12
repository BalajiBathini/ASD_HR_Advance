from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ApplicantEmployeeContractWizard(models.TransientModel):
    _name = 'applicant.employee.contract.wizard'
    _description = 'Applicant Employee & Contract Wizard'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant')
    candidate_id = fields.Many2one('hr.candidate', string='Candidate')
    
    name = fields.Char('Employee Name', required=True)
    email = fields.Char('Work Email')
    phone = fields.Char('Work Phone')
    job_id = fields.Many2one('hr.job', string='Job Position')
    department_id = fields.Many2one('hr.department', string='Department')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', 
        default=lambda self: self.env.company.currency_id
    )
    main_ctc = fields.Monetary('Main CTC (Annual)', currency_field='currency_id')
    monthly_ctc = fields.Monetary('Monthly CTC', compute='_compute_monthly_ctc', currency_field='currency_id', store=True)

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure', required=True)
    contract_start_date = fields.Date('Contract Start Date', required=True, default=fields.Date.context_today)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', required=True, default='single')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        marital_map = {
            'yes': 'married',
            'no': 'single'
        }

        if active_model == 'hr.applicant' and active_id:
            applicant = self.env['hr.applicant'].browse(active_id)
            res.update({
                'applicant_id': applicant.id,
                'candidate_id': applicant.candidate_id.id,
                'name': applicant.partner_name or (applicant.candidate_id and applicant.candidate_id.partner_name) or '',
                'email': applicant.email_from or (applicant.candidate_id and applicant.candidate_id.email_from) or '',
                'phone': applicant.partner_phone or (applicant.candidate_id and applicant.candidate_id.mobile_no) or '',
                'job_id': applicant.job_id.id if applicant.job_id else False,
                'department_id': applicant.department_id.id if applicant.department_id else False,
                'main_ctc': applicant.ctc or applicant.salary_expected or (applicant.candidate_id and applicant.candidate_id.ctc) or 0.0,
                'marital': marital_map.get(applicant.candidate_id.marital_status, 'single') if applicant.candidate_id else 'single'
            })
        elif active_model == 'hr.candidate' and active_id:
            candidate = self.env['hr.candidate'].browse(active_id)
            res.update({
                'candidate_id': candidate.id,
                'name': candidate.partner_name or '',
                'email': candidate.email_from or '',
                'phone': candidate.mobile_no or candidate.partner_phone or '',
                'main_ctc': candidate.ctc or candidate.salary_expected or 0.0,
                'marital': marital_map.get(candidate.marital_status, 'single')
            })
        return res

    @api.depends('main_ctc')
    def _compute_monthly_ctc(self):
        for rec in self:
            rec.monthly_ctc = rec.main_ctc / 12.0 if rec.main_ctc else 0.0

    def action_create(self):
        self.ensure_one()

        if self.candidate_id:
            # Create partner if missing similar to standard create_employee_from_candidate
            if not self.candidate_id.partner_id:
                if not self.candidate_id.partner_name:
                    self.candidate_id.partner_name = self.name
                self.candidate_id.partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': self.candidate_id.partner_name,
                    'email': self.candidate_id.email_from,
                })

            employee_vals = self.candidate_id._get_employee_create_vals()
        else:
            employee_vals = {}

        employee_vals.update({
            'name': self.name,
            'work_email': self.email,
            'work_phone': self.phone,
            'marital': self.marital,
        })
        
        # In Odoo, company.email is used as fallback in standard applicant flow
        if not self.email and self.department_id and self.department_id.company_id.email:
             employee_vals['work_email'] = self.department_id.company_id.email

        if self.job_id:
            employee_vals['job_id'] = self.job_id.id
            employee_vals['job_title'] = self.job_id.name
        if self.department_id:
            employee_vals['department_id'] = self.department_id.id

        employee = self.env['hr.employee'].create(employee_vals)

        contract_vals = {
            'name': f"{employee.name} Contract",
            'employee_id': employee.id,
            'department_id': self.department_id.id,
            'job_id': self.job_id.id,
            'struct_id': self.struct_id.id,
            'wage': self.monthly_ctc,
            'date_start': self.contract_start_date,
            'state': 'draft',
        }
        
        # Link contract to employee
        self.env['hr.contract'].create(contract_vals)

        # Update candidate / applicant
        if self.candidate_id:
            self.candidate_id.employee_id = employee.id
        if self.applicant_id:
            self.applicant_id.employee_id = employee.id

        action = self.env['ir.actions.act_window']._for_xml_id('hr.open_view_employee_list')
        action['res_id'] = employee.id
        action['view_mode'] = 'form'
        action['views'] = [(False, 'form')]
        return action
