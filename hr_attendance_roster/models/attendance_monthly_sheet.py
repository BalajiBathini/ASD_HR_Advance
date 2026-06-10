from odoo import models, fields, api
from datetime import date, timedelta
import calendar

class AttendanceMonthlySheet(models.Model):
    _name = 'attendance.monthly.sheet'
    _description = 'Monthly Attendance Sheet'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True)
    year = fields.Char(string='Year', required=True)

    # Days
    day_1 = fields.Char(string='1')
    day_2 = fields.Char(string='2')
    day_3 = fields.Char(string='3')
    day_4 = fields.Char(string='4')
    day_5 = fields.Char(string='5')
    day_6 = fields.Char(string='6')
    day_7 = fields.Char(string='7')
    day_8 = fields.Char(string='8')
    day_9 = fields.Char(string='9')
    day_10 = fields.Char(string='10')
    day_11 = fields.Char(string='11')
    day_12 = fields.Char(string='12')
    day_13 = fields.Char(string='13')
    day_14 = fields.Char(string='14')
    day_15 = fields.Char(string='15')
    day_16 = fields.Char(string='16')
    day_17 = fields.Char(string='17')
    day_18 = fields.Char(string='18')
    day_19 = fields.Char(string='19')
    day_20 = fields.Char(string='20')
    day_21 = fields.Char(string='21')
    day_22 = fields.Char(string='22')
    day_23 = fields.Char(string='23')
    day_24 = fields.Char(string='24')
    day_25 = fields.Char(string='25')
    day_26 = fields.Char(string='26')
    day_27 = fields.Char(string='27')
    day_28 = fields.Char(string='28')
    day_29 = fields.Char(string='29')
    day_30 = fields.Char(string='30')
    day_31 = fields.Char(string='31')

    # Summary
    present_days = fields.Float(string='Present Days', compute='_compute_summary', store=True)
    weekly_off_days = fields.Float(string='Weekly Off Days', compute='_compute_summary', store=True)
    public_holiday_days = fields.Float(string='Public Holiday Days', compute='_compute_summary', store=True)
    leave_days = fields.Float(string='Leave Days', compute='_compute_summary', store=True)
    absent_days = fields.Float(string='Absent Days', compute='_compute_summary', store=True)
    lop_days = fields.Float(string='LOP Days', compute='_compute_summary', store=True)
    
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_summary', store=True)
    overtime_hours = fields.Float(string='Overtime Hours', compute='_compute_summary', store=True)
    
    total_payable_days = fields.Float(string='Total Payable Days', compute='_compute_summary', store=True)
    total_payable_hours = fields.Float(string='Total Payable Hours', compute='_compute_summary', store=True)

    def _get_leave_code(self, leave_name):
        name = (leave_name or '').upper()
        if 'SICK' in name: return 'SL'
        if 'CASUAL' in name: return 'CL'
        if 'PRIVILEGE' in name: return 'PL'
        if 'LOSS' in name or 'UNPAID' in name: return 'LOP'
        return 'L'

    def action_populate_attendance(self):
        for record in self:
            year = int(record.year)
            month = int(record.month)
            _, num_days = calendar.monthrange(year, month)
            
            start_date = date(year, month, 1)
            end_date = date(year, month, num_days)
            
            # Fetch Leaves
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'validate'),
                ('date_from', '<=', end_date),
                ('date_to', '>=', start_date)
            ])
            
            # Fetch Public Holidays
            domain_ph = [('date', '>=', start_date), ('date', '<=', end_date)]
            holidays = self.env['attendance.public.holiday'].search(domain_ph)
            
            # Fetch Weekly Off Plans
            wo_plans = self.env['attendance.weekoff.plan'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date_from', '<=', end_date),
                '|', ('date_to', '=', False), ('date_to', '>=', start_date)
            ])

            # Fetch Attendances
            from datetime import datetime, time
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', record.employee_id.id),
                ('check_in', '>=', start_dt),
                ('check_in', '<=', end_dt)
            ])

            worked_hrs_total = 0.0
            
            for day in range(1, 32):
                field_name = f'day_{day}'
                
                if day > num_days:
                    setattr(record, field_name, False)
                    continue
                
                current_date = date(year, month, day)
                status = ''
                
                # 1. Leave
                leave_found = False
                for lv in leaves:
                    if lv.request_date_from <= current_date <= lv.request_date_to:
                        status = self._get_leave_code(lv.holiday_status_id.name)
                        if getattr(lv.holiday_status_id, 'is_unpaid', False): 
                            status = 'LOP'
                        leave_found = True
                        break
                if leave_found:
                    setattr(record, field_name, status)
                    continue
                
                # 2. Public Holiday
                ph_found = False
                for ph in holidays:
                    if ph.date == current_date:
                        if not ph.department_id or ph.department_id.id == record.department_id.id:
                            status = 'PH'
                            ph_found = True
                            break
                if ph_found:
                    setattr(record, field_name, status)
                    continue
                
                # 3. Weekly Off
                wo_found = False
                for wo in wo_plans:
                    if (wo.date_from <= current_date and 
                        (not wo.date_to or wo.date_to >= current_date)):
                        if str(current_date.weekday()) == wo.weekoff_day:
                            status = 'WO'
                            wo_found = True
                            break
                if wo_found:
                    setattr(record, field_name, status)
                    continue
                
                # 4. Attendance
                day_att = [a for a in attendances if a.check_in.date() == current_date]
                if day_att:
                    # Could set shift code instead if shifts are assigned, but for now P
                    status = 'P'
                    worked_hrs_total += sum(a.worked_hours for a in day_att)
                else:
                    status = 'A' if current_date <= date.today() else ''

                setattr(record, field_name, status)

            record.worked_hours = worked_hrs_total
            # Compute summary once values are set
            record._compute_summary()

    @api.depends('day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6', 'day_7', 'day_8', 'day_9', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                 'worked_hours')
    def _compute_summary(self):
        for record in self:
            p_days = wo_days = ph_days = l_days = a_days = lop_days = 0.0
            for day in range(1, 32):
                val = getattr(record, f'day_{day}')
                if not val:
                    continue
                val = val.upper()
                if val in ['P', 'P1', 'P2', 'P3', 'PG']: p_days += 1
                elif val == 'WO': wo_days += 1
                elif val == 'PH': ph_days += 1
                elif val == 'LOP': lop_days += 1
                elif val == 'A': a_days += 1
                elif val == 'HD': p_days += 0.5; l_days += 0.5  # Example for Half day
                else: l_days += 1 # Any other leave
            
            record.present_days = p_days
            record.weekly_off_days = wo_days
            record.public_holiday_days = ph_days
            record.leave_days = l_days
            record.absent_days = a_days
            record.lop_days = lop_days
            
            record.total_payable_days = p_days + wo_days + ph_days + l_days
            
            company = record.employee_id.company_id
            daily_hours = company.asd_daily_working_hours if hasattr(company, 'asd_daily_working_hours') and company.asd_daily_working_hours else 8.0
            
            record.total_payable_hours = record.total_payable_days * daily_hours
            
            norm_hours = p_days * daily_hours 
            overtime = record.worked_hours - norm_hours
            record.overtime_hours = overtime if overtime > 0 else 0.0

    @api.model
    def cron_generate_monthly_sheets(self):
        today = date.today()
        # Always run for current month
        month_str = str(today.month)
        year_str = str(today.year)
        
        employees = self.env['hr.employee'].search([('company_id', '!=', False)])
        for emp in employees:
            sheet = self.search([('employee_id', '=', emp.id), ('month', '=', month_str), ('year', '=', year_str)], limit=1)
            if not sheet:
                sheet = self.create({
                    'employee_id': emp.id,
                    'month': month_str,
                    'year': year_str
                })
            sheet.action_populate_attendance()
