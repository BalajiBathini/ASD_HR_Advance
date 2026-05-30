from odoo import models, fields, api

class BulkBonusWizard(models.TransientModel):
    _name = 'bulk.bonus.wizard'
    _description = 'Bulk Bonus Wizard'

    apply_to_all = fields.Boolean(string='Apply to All Employees', default=False)
    employee_ids = fields.Many2many('hr.employee', string='Selected Employees')
    
    name = fields.Char(string='Bonus Name', required=True)
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
    bonus_month = fields.Date(string='Effective Month', required=True)
    
    def action_apply_bonus(self):
        self.ensure_one()
        employees = self.env['hr.employee'].search([]) if self.apply_to_all else self.employee_ids
        
        bonus_vals = []
        for emp in employees:
            bonus_vals.append({
                'name': self.name,
                'employee_id': emp.id,
                'bonus_type': self.bonus_type,
                'calculation_base': self.calculation_base,
                'amount': self.amount,
                'bonus_month': self.bonus_month,
                'state': 'draft' # HR can edit values before approving
            })
            
        if bonus_vals:
            self.env['hr.bonus'].create(bonus_vals)
