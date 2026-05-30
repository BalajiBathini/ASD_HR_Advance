from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import date
import calendar

class AttendanceMonthlyBalance(models.Model):
    _name = 'attendance.monthly.balance'
    _description = 'Working Hours Ledger'
    _rec_name = 'month_year'
    _order = 'date_start desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    month_year = fields.Char(string='Month/Year', compute='_compute_month_year', store=True)
    
    norm_hours = fields.Float(string='Government Standard Hours', tracking=True)
    actual_worked_hours = fields.Float(string='Actual Worked Hours', tracking=True)
    overtime_hours = fields.Float(string='Overtime Hours', compute='_compute_hours', store=True)

    previous_balance_hours = fields.Float(string='Previous Balance Hours', default=0.0)
    total_available_hours = fields.Float(string='Total Available Hours', compute='_compute_total_available_hours', store=True)
    
    consumed_hours = fields.Float(string='Consumed Hours', default=0.0, tracking=True)
    remaining_balance_hours = fields.Float(string='Remaining Balance Hours', compute='_compute_remaining_balance_hours', store=True)
    
    is_salary_eligible = fields.Boolean(string='Salary Eligible', compute='_compute_is_salary_eligible', store=True)
    
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True)

    @api.depends('date_start')
    def _compute_month_year(self):
        for record in self:
            if record.date_start:
                record.month_year = record.date_start.strftime("%B %Y")
            else:
                record.month_year = ""

    @api.depends('actual_worked_hours', 'norm_hours')
    def _compute_hours(self):
        for record in self:
            overtime = record.actual_worked_hours - record.norm_hours
            record.overtime_hours = overtime if overtime > 0 else 0.0

    @api.onchange('employee_id', 'date_start', 'date_end')
    def _onchange_fetch_attendance_data(self):
        for record in self:
            if record.employee_id and record.date_start and record.date_end:
                company = record.employee_id.company_id
                
                # Fetch Norm Hours
                days_in_month = (record.date_end - record.date_start).days + 1
                working_days = days_in_month - company.asd_weekly_offs_count
                record.norm_hours = working_days * company.asd_daily_working_hours

                # Fetch Actual Worked Hours from HR Attendance
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', record.employee_id._origin.id or record.employee_id.id),
                    ('check_in', '>=', fields.Datetime.to_datetime(record.date_start)),
                    ('check_out', '<', fields.Datetime.to_datetime(record.date_end + relativedelta(days=1)))
                ])
                record.actual_worked_hours = sum(att.worked_hours for att in attendances)

                # Fetch Previous Balance
                last_month_start = record.date_start - relativedelta(months=1)
                prev_balance_record = self.env['attendance.monthly.balance'].search([
                    ('employee_id', '=', record.employee_id._origin.id or record.employee_id.id),
                    ('date_start', '=', last_month_start)
                ], limit=1)
                record.previous_balance_hours = prev_balance_record.remaining_balance_hours if prev_balance_record else 0.0
                
                # Default Consumed Hours to Norm Hours
                record.consumed_hours = record.norm_hours

    @api.depends('previous_balance_hours', 'actual_worked_hours')
    def _compute_total_available_hours(self):
        for record in self:
            record.total_available_hours = record.previous_balance_hours + record.actual_worked_hours

    @api.depends('total_available_hours', 'consumed_hours')
    def _compute_remaining_balance_hours(self):
        for record in self:
            record.remaining_balance_hours = record.total_available_hours - record.consumed_hours

    @api.depends('remaining_balance_hours', 'company_id.asd_minimum_payable_hours', 'total_available_hours', 'norm_hours')
    def _compute_is_salary_eligible(self):
        for record in self:
            min_hours = record.company_id.asd_minimum_payable_hours
            if min_hours > 0.0:
                record.is_salary_eligible = record.total_available_hours >= min_hours
            else:
                record.is_salary_eligible = record.total_available_hours >= record.norm_hours

    @api.model
    def compute_monthly_balances(self, validation_date=False):
        """Cron method to compute last month balances for all employees."""
        if not validation_date:
            validation_date = fields.Date.today()
        
        # Determine the previous month
        first_day_of_current_month = validation_date.replace(day=1)
        last_day_of_prev_month = first_day_of_current_month - relativedelta(days=1)
        first_day_of_prev_month = last_day_of_prev_month.replace(day=1)

        employees = self.env['hr.employee'].search([('company_id', '!=', False)])
        
        for employee in employees:
            company = employee.company_id
            if not company.asd_carry_forward_enabled:
                continue
                
            # Check if record already exists
            existing = self.search([
                ('employee_id', '=', employee.id),
                ('date_start', '=', first_day_of_prev_month),
                ('date_end', '=', last_day_of_prev_month)
            ])
            if existing:
                continue

            # Calculate Norm Hours
            days_in_month = (last_day_of_prev_month - first_day_of_prev_month).days + 1
            working_days = days_in_month - company.asd_weekly_offs_count
            norm_hours = working_days * company.asd_daily_working_hours

            # Calculate Actual Worked Hours from HR Attendance
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', fields.Datetime.to_datetime(first_day_of_prev_month)),
                ('check_out', '<', fields.Datetime.to_datetime(first_day_of_current_month))
            ])
            actual_worked = sum(att.worked_hours for att in attendances)

            # Get Previous Balance
            last_month_start = first_day_of_prev_month - relativedelta(months=1)
            prev_balance_record = self.search([
                ('employee_id', '=', employee.id),
                ('date_start', '=', last_month_start)
            ], limit=1)
            
            prev_balance_hours = prev_balance_record.remaining_balance_hours if prev_balance_record else 0.0

            # Create Record
            self.create({
                'employee_id': employee.id,
                'date_start': first_day_of_prev_month,
                'date_end': last_day_of_prev_month,
                'norm_hours': norm_hours,
                'actual_worked_hours': actual_worked,
                'previous_balance_hours': prev_balance_hours,
                'consumed_hours': norm_hours
            })
