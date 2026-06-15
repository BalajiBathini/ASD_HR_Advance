from odoo import models, fields, api, exceptions

class HrLeaveEncashment(models.Model):
    _name = 'hr.leave.encashment'
    _description = 'Leave Encashment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', required=True, domain=[('is_encashable', '=', True)])
    el_days = fields.Float(string='Encashment Days', required=True)
    amount = fields.Float(string='Encashment Amount', compute='_compute_amount', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.depends('el_days', 'employee_id')
    def _compute_amount(self):
        for record in self:
            if record.employee_id and record.el_days:
                # Basic calculation: Montly Wage / 30 * el_days
                # Requires hr_payroll to get contract wage
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'open')
                ], limit=1)
                
                if contract:
                    daily_wage = contract.wage / 30.0
                    record.amount = daily_wage * record.el_days
                else:
                    record.amount = 0.0
            else:
                record.amount = 0.0

    @api.model_create_multi
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.leave.encashment') or 'New'
        return super(HrLeaveEncashment, self).create(vals)
        
    def action_submit(self):
        self.state = 'submit'

    def action_approve(self):
        # Optional: check if employee has enough leave balance
        self.state = 'approve'

    def action_done(self):
        for record in self:
            # Deduct the leave balance by creating an allocation of negative days
            # or creating a leave request that is marked as 'encashment' (simpler approach: negative allocation)
            allocation_vals = {
                'name': f"Encashment Deduction: {record.name}",
                'employee_id': record.employee_id.id,
                'holiday_status_id': record.leave_type_id.id,
                'number_of_days': -record.el_days,
                'state': 'validate',
                'holiday_type': 'employee'
            }
            self.env['hr.leave.allocation'].create(allocation_vals)
            record.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'
