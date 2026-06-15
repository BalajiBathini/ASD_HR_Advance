from odoo import models, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _accrue_el_monthly(self):
        """ Cron method to automatically accrue EL (e.g. 1.25 days) every month. """
        # Find the Earned Leave type
        el_type = self.env['hr.leave.type'].search([('name', '=', 'Earned Leave (EL)')], limit=1)
        if not el_type:
            # Maybe search by code or other identifier if name changes
            el_type = self.env['hr.leave.type'].search([('is_carry_forward', '=', True), ('is_encashable', '=', True)], limit=1)

        if el_type:
            employees = self.search([('active', '=', True)])
            for emp in employees:
                allocation_vals = {
                    'name': 'Monthly EL Accrual',
                    'employee_id': emp.id,
                    'holiday_status_id': el_type.id,
                    'number_of_days': 1.25,
                    'state': 'validate',
                    'holiday_type': 'employee'
                }
                self.env['hr.leave.allocation'].create(allocation_vals)
