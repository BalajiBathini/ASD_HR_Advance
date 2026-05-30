from odoo import models, fields, api

class SalaryAttachment(models.Model):
    _name = 'salary.attachment'
    _description = 'Salary Attachment'
    
    name = fields.Char(string='Description', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    attachment_type = fields.Selection([
        ('loan', 'Loan'),
        ('advance', 'Salary Advance'),
        ('other', 'Other Deduction')
    ], string='Attachment Type', required=True, default='loan')
    
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id', help='Total loan/advance amount or fixed deduction amount')
    emi_amount = fields.Monetary(string='EMI Amount', currency_field='currency_id', help='Amount to deduct each month')
    recovered_amount = fields.Monetary(string='Recovered Amount', currency_field='currency_id', default=0.0)
    balance_amount = fields.Monetary(string='Balance Amount', compute='_compute_balance', store=True, currency_field='currency_id')
    
    is_percentage = fields.Boolean(string='Is Percentage?', help='Only used for Other Deductions')
    percentage = fields.Float(string='Percentage', help='Only used if deduction is percentage based')
    
    start_month = fields.Date(string='Start Month', required=True, help='When to start deducting')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    currency_id = fields.Many2one(related='company_id.currency_id')

    @api.depends('total_amount', 'recovered_amount')
    def _compute_balance(self):
        for rec in self:
            if rec.attachment_type in ['loan', 'advance']:
                rec.balance_amount = rec.total_amount - rec.recovered_amount
            else:
                rec.balance_amount = 0.0

    def action_confirm(self):
        for rec in self:
            rec.state = 'active'
            
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            
    def mark_as_completed(self):
        for rec in self:
            rec.state = 'completed'
