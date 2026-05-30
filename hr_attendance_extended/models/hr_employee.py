from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_balance_ids = fields.One2many('attendance.monthly.balance', 'employee_id', string='Working Hours Ledgers')

    def action_view_attendance_ledger(self):
        self.ensure_one()
        return {
            'name': 'Working Hours Ledger',
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.monthly.balance',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
