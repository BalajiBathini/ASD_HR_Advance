from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'

#     first_contract_date = fields.Date(string='First Contract Date', default=fields.Date.today())

#     @api.model
#     def create(self, vals):
#         if 'first_contract_date' not in vals or not vals['first_contract_date']:
#             vals['first_contract_date'] = fields.Date.today()
#         return super(HrEmployee, self).create(vals)

class HrInductionStage(models.Model):
    _name = 'hr.induction.stage'
    _description = 'HR Induction Stage'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=4)
    fold = fields.Boolean(string='Folded in Kanban', default=False)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        index=True,
    )

    _sql_constraints = [
        ('name_company_unique', 'unique(name, company_id)', 'Stage names must be unique per company.'),
    ]

class HrInductionDepartmentLine(models.Model):
    _name = 'hr.induction.department.line'
    _description = 'HR Induction Department Line'
    _rec_name = 'department_id'
    _check_company_auto = True

    sr_no = fields.Integer(string='Sr. No.', readonly=True, required=True, copy=False)
    induction_id = fields.Many2one('hr.induction', string='Induction', ondelete='cascade', check_company=True)
    company_id = fields.Many2one('res.company', string='Company', related='induction_id.company_id', store=True, readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True, check_company=True)
    induction_datetime_from = fields.Datetime(string='Induction From')
    induction_datetime_to = fields.Datetime(string='Induction To')
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    assigned_to = fields.Many2one('hr.employee', string='Assigned To', check_company=True)
    remarks = fields.Text(string='Remarks')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    stage_id = fields.Many2one('hr.induction.stage', string='Stage', default=lambda self: self._default_stage())
    stage_name = fields.Char(string='Stage Name', compute='_compute_stage_name', store=True)
    attendance_marked = fields.Boolean(string='Attendance Marked', default=False)
    previous_stage_id = fields.Many2one('hr.induction.stage', string='Previous Stage', readonly=True)

    _sql_constraints = [
        ('sr_company_unique', 'unique(sr_no, company_id)', 'Department line sequence must be unique per company.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'sr_no' not in vals:
                induction = self.env['hr.induction'].browse(vals.get('induction_id')) if vals.get('induction_id') else False
                company_id = induction.company_id.id if induction and induction.company_id else self.env.company.id
                seq_str = self.env['ir.sequence'].with_company(company_id).next_by_code('hr.induction.department.line')
                vals['sr_no'] = int(seq_str) if seq_str else 1
        return super(HrInductionDepartmentLine, self).create(vals_list)

    def _default_stage(self):
        return self.env['hr.induction.stage'].search([
            ('name', '=', 'Draft'),
            ('company_id', 'in', [self.env.company.id, False])
        ], limit=1)

    @api.depends('stage_id')
    def _compute_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name if record.stage_id else False

    @api.depends('induction_datetime_from', 'induction_datetime_to')
    def _compute_duration(self):
        for record in self:
            if record.induction_datetime_from and record.induction_datetime_to:
                duration = record.induction_datetime_to - record.induction_datetime_from
                record.duration = duration.total_seconds() / 3600
            else:
                record.duration = 0.0

    @api.constrains('induction_datetime_from', 'induction_datetime_to')
    def _check_time_range(self):
        for record in self:
            if record.induction_datetime_from and record.induction_datetime_to:
                if record.induction_datetime_from >= record.induction_datetime_to:
                    raise ValidationError("End time must be after start time.")

    # def action_mark_attendance(self):
    #     self.ensure_one()
    #     scheduled_stage = self.env['hr.induction.stage'].search([('name', '=', 'Scheduled')], limit=1)
    #     if scheduled_stage:
    #         self.write({
    #             'attendance_marked': True,
    #             'previous_stage_id': self.stage_id.id,
    #             'stage_id': scheduled_stage.id
    #         })
    
    def action_mark_attendance(self):
        self.ensure_one()
        # Validate required fields
        error_messages = []
        if not self.induction_datetime_from:
            error_messages.append("The 'Duration From' field must be filled.")
        if not self.induction_datetime_to:
            error_messages.append("The 'Duration To' field must be filled.")
        if not self.assigned_to:
            error_messages.append("The 'Assigned To' field must be filled.")
        if not self.remarks:
            error_messages.append("The 'Remarks' field must be filled.")
        
        if error_messages:
            raise ValidationError("\n".join(error_messages))
        
        # Proceed with marking attendance if all fields are filled
        scheduled_stage = self._stage_for_name('Scheduled')
        if scheduled_stage:
            self.write({
                'attendance_marked': True,
                'previous_stage_id': self.stage_id.id,
                'stage_id': scheduled_stage.id
            })


    def action_complete(self):
        self.ensure_one()
        completed_stage = self._stage_for_name('Completed')
        if completed_stage:
            self.write({
                'previous_stage_id': self.stage_id.id,
                'stage_id': completed_stage.id
            })

    def action_cancel(self):
        self.ensure_one()
        cancelled_stage = self._stage_for_name('Cancelled')
        if cancelled_stage:
            self.write({
                'previous_stage_id': self.stage_id.id,
                'stage_id': cancelled_stage.id,
                'attendance_marked': False
            })

    def action_undo(self):
        self.ensure_one()
        if not self.previous_stage_id:
            # Get the default stage based on current stage
            if self.stage_name == 'Scheduled':
                previous_stage = self._stage_for_name('Draft')
                vals = {
                    'stage_id': previous_stage.id if previous_stage else self.stage_id.id,
                    'attendance_marked': False
                }
                self.write(vals)
            elif self.stage_name == 'Completed':
                previous_stage = self._stage_for_name('Scheduled')
                if previous_stage:
                    self.write({'stage_id': previous_stage.id})
            elif self.stage_name == 'Cancelled':
                previous_stage = self._stage_for_name('Draft')
                if previous_stage:
                    self.write({'stage_id': previous_stage.id})
            else:
                raise UserError("No previous stage to undo to.")
        else:
            # Use the stored previous stage
            vals = {
                'stage_id': self.previous_stage_id.id,
                'previous_stage_id': False
            }
            if self.stage_name == 'Scheduled' and self.previous_stage_id.name == 'Draft':
                vals['attendance_marked'] = False
            self.write(vals)

    def _stage_for_name(self, name):
        company = self.company_id or self.induction_id.company_id or self.env.company
        return self.env['hr.induction.stage'].search([
            ('name', '=', name),
            ('company_id', 'in', [company.id, False])
        ], limit=1)

    @api.constrains('department_id', 'company_id')
    def _check_department_company(self):
        for record in self:
            dept_company = record.department_id.company_id
            if dept_company and dept_company != record.company_id:
                raise ValidationError(_('The department must belong to the same company as the induction.'))

    @api.constrains('assigned_to', 'company_id')
    def _check_assigned_company(self):
        for record in self:
            emp_company = record.assigned_to.company_id if record.assigned_to else False
            if emp_company and emp_company != record.company_id:
                raise ValidationError(_('Assigned employees must belong to the same company as the induction.'))

class HrInduction(models.Model):
    _name = 'hr.induction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Induction'
    _order = 'sr_no desc'
    _check_company_auto = True

    sr_no = fields.Integer(string='Sr. No.', readonly=True, required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, tracking=True, index=True)
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True, check_company=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    employee_code = fields.Char(related='employee_id.barcode', string='Employee Code', readonly=True, store=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', readonly=True, store=True)
    hod_id = fields.Many2one(related='department_id.manager_id', string='HOD', readonly=True, store=True)
    joining_date = fields.Date(string='Joining Date', related='employee_id.joining_date', readonly=True, store=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    stage_id = fields.Many2one('hr.induction.stage', string='Stage', default=lambda self: self._default_stage(), tracking=True)
    stage_name = fields.Char(string='Stage Name', compute='_compute_stage_name', store=True)
    department_line_ids = fields.One2many('hr.induction.department.line', 'induction_id', string='Department Inductions')
    previous_stage_id = fields.Many2one('hr.induction.stage', string='Previous Stage', readonly=True)

    _sql_constraints = [
        ('sr_company_unique', 'unique(sr_no, company_id)', 'Induction sequence must be unique per company.'),
    ]

    @api.depends('stage_id')
    def _compute_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name if record.stage_id else False

    @api.depends('employee_id', 'sr_no')
    def _compute_name(self):
        for record in self:
            if record.employee_id:
                record.name = f"Induction - {record.employee_id.name} - {record.sr_no}"
            else:
                record.name = "New Induction"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id') or self.env.company.id
            vals['company_id'] = company_id
            if 'sr_no' not in vals:
                seq_str = self.env['ir.sequence'].with_company(company_id).next_by_code('hr.induction')
                vals['sr_no'] = int(seq_str) if seq_str else 1
                
        records = super(HrInduction, self).create(vals_list)
        
        for record in records:
            departments = self.env['hr.department'].search([('company_id', 'in', [record.company_id.id, False])])
            department_lines = [(0, 0, {'department_id': dept.id}) for dept in departments]
            record.department_line_ids = department_lines
            
        return records

    def _default_stage(self):
        return self.env['hr.induction.stage'].search([
            ('name', '=', 'Draft'),
            ('company_id', 'in', [self.env.company.id, False])
        ], limit=1)

    def action_schedule(self):
        self.ensure_one()
        scheduled_stage = self._stage_for_name('Scheduled')
        if scheduled_stage:
            self.write({
                'previous_stage_id': self.stage_id.id,
                'stage_id': scheduled_stage.id
            })
            self._send_induction_email()

    def action_complete(self):
        self.ensure_one()
        completed_stage = self._stage_for_name('Completed')
        if completed_stage:
            self.write({
                'previous_stage_id': self.stage_id.id,
                'stage_id': completed_stage.id
            })

    def action_cancel(self):
        self.ensure_one()
        cancelled_stage = self._stage_for_name('Cancelled')
        if cancelled_stage:
            self.write({
                'previous_stage_id': self.stage_id.id,
                'stage_id': cancelled_stage.id
            })

    def action_undo(self):
        self.ensure_one()
        if not self.previous_stage_id:
            # Get the default stage based on current stage
            if self.stage_name == 'Scheduled':
                previous_stage = self._stage_for_name('Draft')
                if previous_stage:
                    self.write({'stage_id': previous_stage.id})
            elif self.stage_name == 'Completed':
                previous_stage = self._stage_for_name('Scheduled')
                if previous_stage:
                    self.write({'stage_id': previous_stage.id})
            elif self.stage_name == 'Cancelled':
                previous_stage = self._stage_for_name('Draft')
                if previous_stage:
                    self.write({'stage_id': previous_stage.id})
            else:
                raise UserError("No previous stage to undo to.")
        else:
            # Use the stored previous stage
            self.write({
                'stage_id': self.previous_stage_id.id,
                'previous_stage_id': False
            })

    def _send_induction_email(self):
        template = self.env.ref('hr_induction.mail_template_induction_scheduled')
        if template:
            template.send_mail(self.id, force_send=True)

    def _stage_for_name(self, name):
        company = self.company_id or self.env.company
        return self.env['hr.induction.stage'].search([
            ('name', '=', name),
            ('company_id', 'in', [company.id, False])
        ], limit=1)

    @api.constrains('employee_id', 'company_id')
    def _check_employee_company(self):
        for record in self:
            emp_company = record.employee_id.company_id if record.employee_id else False
            if emp_company and emp_company != record.company_id:
                raise ValidationError(_('The employee must belong to the same company as the induction.'))

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    induction_session_count = fields.Integer(string='Induction Sessions', compute='_compute_induction_session_count')

    def _compute_induction_session_count(self):
        for department in self:
            department.induction_session_count = self.env['hr.induction.department.line'].search_count([('department_id', '=', department.id)])

    def action_view_induction_sessions(self):
        self.ensure_one()
        return {
            'name': 'Induction Sessions',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.induction.department.line',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
        }