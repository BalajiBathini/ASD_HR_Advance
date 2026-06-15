from odoo import models, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrAttendance, self).create(vals_list)
        records._check_and_generate_comp_off()
        return records

    def write(self, vals):
        res = super(HrAttendance, self).write(vals)
        if 'check_out' in vals:
            self._check_and_generate_comp_off()
        return res

    def _check_and_generate_comp_off(self):
        comp_off_type = self.env['hr.leave.type'].search([('name', 'ilike', 'Compensatory Off')], limit=1)
        if not comp_off_type:
            return

        for attendance in self:
            if attendance.check_in and attendance.check_out and attendance.worked_hours >= 4.0:
                # Need to check if date was a weekend or holiday
                date = attendance.check_in.date()
                employee = attendance.employee_id
                
                # Check Resource Calendar
                resource_calendar = employee.resource_calendar_id
                tz = employee.tz or 'UTC'
                # if there is no calendar, we assume weekends are holidays?
                if resource_calendar:
                    import pytz
                    from odoo import fields
                    tz_obj = pytz.timezone(tz)
                    local_date = pytz.utc.localize(attendance.check_in).astimezone(tz_obj).date()
                    start_dt = tz_obj.localize(fields.Datetime.from_string(f"{local_date} 00:00:00")).astimezone(pytz.UTC)
                    end_dt = tz_obj.localize(fields.Datetime.from_string(f"{local_date} 23:59:59")).astimezone(pytz.UTC)
                    intervals = resource_calendar._work_intervals_batch(start_dt, end_dt)
                    is_working_day = bool(intervals[False])
                else:
                    # fallback to weekend check
                    is_working_day = date.weekday() < 5 # 0-4 is Mon-Fri

                # Check Holiday Calendar
                holiday = self.env['hr.holiday.calendar'].search([
                    ('date', '=', date)
                ], limit=1)

                is_off_day = (not is_working_day) or bool(holiday)

                if is_off_day:
                    # Generate Comp Off Allocation
                    # First check if an allocation already exists for this attendance date to prevent duplicates
                    existing = self.env['hr.leave.allocation'].search([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', comp_off_type.id),
                        ('name', '=', f'Comp Off for {date}')
                    ])
                    if not existing:
                        days = 0.5 if attendance.worked_hours < 8.0 else 1.0
                        allocation_vals = {
                            'name': f'Comp Off for {date}',
                            'employee_id': employee.id,
                            'holiday_status_id': comp_off_type.id,
                            'number_of_days': days,
                            'state': 'validate',
                            'holiday_type': 'employee'
                        }
                        self.env['hr.leave.allocation'].create(allocation_vals)
