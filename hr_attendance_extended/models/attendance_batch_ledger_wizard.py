from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import date

class AttendanceBatchLedger(models.Model):
    _name = 'attendance.batch.ledger'
    _description = 'Batch Work Hour Ledger'

    name = fields.Char(string='Reference', required=True, copy=False, default='New')

    date_start = fields.Date(string='From', required=True, default=lambda self: date.today().replace(day=1))
    date_end = fields.Date(string='To', required=True, default=lambda self: (date.today().replace(day=1) + relativedelta(months=1, days=-1)))
    all_employees = fields.Boolean(string='All Employees', default=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')

    def action_generate_ledgers(self):
        self.ensure_one()
        
        # Decide which employees to iterate over
        if self.all_employees:
            employees = self.env['hr.employee'].search([('company_id', '!=', False)])
        else:
            employees = self.employee_ids

        for employee in employees:
            company = employee.company_id
            if not company.asd_carry_forward_enabled:
                continue
                
            # Check if record already exists for exact exact date
            existing = self.env['attendance.monthly.balance'].search([
                ('employee_id', '=', employee.id),
                ('date_start', '=', self.date_start),
                ('date_end', '=', self.date_end)
            ], limit=1)
            
            if existing:
                continue

            # Calculate Norm Hours
            days_in_month = (self.date_end - self.date_start).days + 1
            working_days = days_in_month - (company.asd_weekly_offs_count or 0)
            norm_hours = working_days * (company.asd_daily_working_hours or 0.0)

            # Calculate Actual Worked Hours from HR Attendance
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', fields.Datetime.to_datetime(self.date_start)),
                ('check_out', '<', fields.Datetime.to_datetime(self.date_end + relativedelta(days=1)))
            ])
            actual_worked = sum(att.worked_hours for att in attendances)

            # Get Previous Balance
            last_month_start = self.date_start - relativedelta(months=1)
            prev_balance_record = self.env['attendance.monthly.balance'].search([
                ('employee_id', '=', employee.id),
                ('date_start', '=', last_month_start)
            ], limit=1)
            
            prev_balance_hours = prev_balance_record.remaining_balance_hours if prev_balance_record else 0.0

            # Create Record
            self.env['attendance.monthly.balance'].create({
                'employee_id': employee.id,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'norm_hours': norm_hours,
                'actual_worked_hours': actual_worked,
                'previous_balance_hours': prev_balance_hours,
                'consumed_hours': norm_hours
            })
        
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = f"Batch Ledger - {vals.get('date_start')} to {vals.get('date_end')}"
        return super().create(vals_list)
