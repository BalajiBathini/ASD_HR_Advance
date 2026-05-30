from odoo import models, fields, api

class HrBonus(models.Model):
    _name = 'hr.bonus'
    _description = 'Employee Bonus'

    name = fields.Char(string='Bonus Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    bonus_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage')
    ], string='Bonus Type', default='fixed', required=True)
    
    calculation_base = fields.Selection([
        ('gross', 'Gross Salary'),
        ('basic', 'Basic Salary'),
        ('net', 'Net Salary')
    ], string='Calculation Base')
    
    amount = fields.Float(string='Amount / Percentage', required=True)
    bonus_month = fields.Date(string='Bonus Month', required=True)
    remarks = fields.Text(string='Remarks')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid')
    ], string='Status', default='draft')
    
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
