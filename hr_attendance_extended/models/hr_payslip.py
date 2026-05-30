from odoo import api, fields, models

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    asd_monthly_balance_id = fields.Many2one('attendance.monthly.balance', string='Working Hours Ledger', readonly=True)
    asd_is_salary_eligible = fields.Boolean(related='asd_monthly_balance_id.is_salary_eligible', string='Salary Eligible')
    
    asd_norm_hours = fields.Float(related='asd_monthly_balance_id.norm_hours', string='Standard Norm Hours')
    asd_actual_worked = fields.Float(related='asd_monthly_balance_id.actual_worked_hours', string='Actual Worked')
    asd_total_available = fields.Float(related='asd_monthly_balance_id.total_available_hours', string='Total Available')
    asd_remaining_balance = fields.Float(related='asd_monthly_balance_id.remaining_balance_hours', string='Carried Forward')

    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        
        for payslip in self:
            if not payslip.employee_id.company_id.asd_carry_forward_enabled:
                continue
            
            # Find the ledger for this payslip's month
            ledger = self.env['attendance.monthly.balance'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('date_start', '<=', payslip.date_from),
                ('date_end', '>=', payslip.date_from)  # Assuming the ledger spans the payslip start date entirely
            ], limit=1)
            
            if ledger:
                payslip.asd_monthly_balance_id = ledger.id
                # Note: The `remaining_balance_hours` is automatically deducted by `norm_hours` in its compute method on the ledger. 
                # Setting `ledger.consumed_hours = ledger.norm_hours` here causes a double deduction. Let's leave it as 0 by default.


        return res

    def _compute_worked_days(self, contract, day_from, day_to):
        res = super(HrPayslip, self)._compute_worked_days(contract, day_from, day_to)
        
        company = contract.company_id
        if company.asd_carry_forward_enabled:
            # First attempt to find the pre-generated custom attendance ledger
            ledger = self.env['attendance.monthly.balance'].search([
                ('employee_id', '=', contract.employee_id.id),
                ('date_start', '<=', day_from.date()),
                ('date_end', '>=', day_from.date())
            ], limit=1)

            if ledger:
                # Use ledger's exact calculated actual worked hours
                res['number_of_hours'] = ledger.actual_worked_hours
                if company.asd_daily_working_hours:
                    res['number_of_days'] = ledger.actual_worked_hours / company.asd_daily_working_hours
                else:
                    res['number_of_days'] = 0.0
            else:
                # Fallback to direct raw biometric attendance summation if no ledger was generated
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('check_in', '>=', day_from),
                    ('check_out', '<', day_to)
                ])
                actual_worked = sum(att.worked_hours for att in attendances)
                res['number_of_hours'] = actual_worked
                if company.asd_daily_working_hours:
                    res['number_of_days'] = actual_worked / company.asd_daily_working_hours
                else:
                    res['number_of_days'] = 0.0
                    
        return res
