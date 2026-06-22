from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # Override standard compute_sheet to use our custom engine instead of hr_payroll rules
    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super().get_inputs(contracts, date_from, date_to)
        
        for contract in contracts:
            # 0. Auto-Heal the Salary Structure to ensure our Custom Global Rules are present
            if contract.struct_id:
                missing_rule_ids = []
                rule_attachments = self.env.ref('employee_bonus_management.hr_rule_salary_attachments', raise_if_not_found=False)
                if rule_attachments and rule_attachments.id not in contract.struct_id.rule_ids.ids:
                    missing_rule_ids.append(rule_attachments.id)
                
                rule_bonuses = self.env.ref('employee_bonus_management.hr_rule_employee_bonuses', raise_if_not_found=False)
                if rule_bonuses and rule_bonuses.id not in contract.struct_id.rule_ids.ids:
                    missing_rule_ids.append(rule_bonuses.id)
                    
                if missing_rule_ids:
                    contract.struct_id.sudo().write({'rule_ids': [(4, rid) for rid in missing_rule_ids]})
            
            # 1. Active Loans & Advances
            attachments = self.env['salary.attachment'].search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', '=', 'active'),
                ('start_month', '<=', date_to)
            ])
            for att in attachments:
                if att.attachment_type in ['loan', 'advance']:
                    deduct_amt = min(att.emi_amount, att.balance_amount)
                    if deduct_amt > 0:
                        res.append({
                            'name': att.name + ' EMI',
                            'code': 'ATT_' + str(att.id),
                            'amount': deduct_amt,
                            'contract_id': contract.id,
                        })
                else: 
                    # Other percentage or fixed deduction
                    deduct_amt = att.total_amount if not att.is_percentage else (contract.wage * att.percentage / 100.0)
                    res.append({
                        'name': att.name,
                        'code': 'ATT_OTHER_' + str(att.id),
                        'amount': deduct_amt,
                        'contract_id': contract.id,
                    })
                        
            # 2. Active Bonuses
            bonuses = self.env['hr.bonus'].search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', '=', 'approved'),
                ('bonus_month', '>=', date_from),
                ('bonus_month', '<=', date_to)
            ])
            for bonus in bonuses:
                bonus_amt = bonus.amount if bonus.bonus_type == 'fixed' else (contract.wage * bonus.amount / 100.0)
                res.append({
                    'name': bonus.name,
                    'code': 'BONUS_' + str(bonus.id),
                    'amount': bonus_amt,
                    'contract_id': contract.id,
                })
        
        return res

    def action_payslip_done(self):
        res = super().action_payslip_done()
        for payslip in self:
            # Update Recovery Balances for Attachments
            # We look at the generated inputs that ended up on the payslip
            for input_line in payslip.input_line_ids:
                if input_line.code and input_line.code.startswith('ATT_') and not input_line.code.startswith('ATT_OTHER_'):
                    # It's a loan or advance
                    att_id_str = input_line.code.split('_')[1]
                    try:
                        att = self.env['salary.attachment'].browse(int(att_id_str))
                        if att.exists() and att.state == 'active':
                            att.recovered_amount += input_line.amount
                            if att.balance_amount <= 0:
                                att.mark_as_completed()
                    except ValueError:
                        pass
                elif input_line.code and input_line.code.startswith('BONUS_'):
                    bonus_id_str = input_line.code.split('_')[1]
                    try:
                        bonus = self.env['hr.bonus'].browse(int(bonus_id_str))
                        if bonus.exists() and bonus.state == 'approved':
                            bonus.state = 'paid'
                    except ValueError:
                        pass
        return res

    def compute_sheet(self):
        for payslip in self:
            if payslip.struct_id:
                missing_rule_ids = []
                rule_attachments = self.env.ref('employee_bonus_management.hr_rule_salary_attachments', raise_if_not_found=False)
                if rule_attachments and rule_attachments.id not in payslip.struct_id.rule_ids.ids:
                    missing_rule_ids.append(rule_attachments.id)
                
                rule_bonuses = self.env.ref('employee_bonus_management.hr_rule_employee_bonuses', raise_if_not_found=False)
                if rule_bonuses and rule_bonuses.id not in payslip.struct_id.rule_ids.ids:
                    missing_rule_ids.append(rule_bonuses.id)
                    
                if missing_rule_ids:
                    payslip.struct_id.sudo().write({'rule_ids': [(4, rid) for rid in missing_rule_ids]})
        
        return super().compute_sheet()
