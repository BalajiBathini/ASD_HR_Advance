from odoo import models, fields, api
from datetime import timedelta

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    sandwich_extra_days = fields.Float(
        string='Sandwich Extra Days', 
        compute='_compute_sandwich_days',
        store=True,
        help="Extra leave days added due to sandwich policy (weekends or public holidays between leave days)."
    )

    @api.depends('date_from', 'date_to', 'employee_id', 'holiday_status_id')
    def _compute_sandwich_days(self):
        for leave in self:
            extra_days = 0.0
            if leave.date_from and leave.date_to and leave.employee_id:
                # We need to find if there are weekends / holidays between date_from and date_to
                # Wait, sandwich policy usually applies if a weekend falls *between* leave days,
                # e.g., leave on Friday and Monday -> Saturday and Sunday become leave days too.
                # In Odoo, if someone takes leave Friday to Monday, date_from=Fri, date_to=Mon. 
                # Ordinary _compute_number_of_days gives 2 days (Fri, Mon) excluding Sat/Sun.
                # If we apply Sandwich, we should just consider the total calendar days from Fri to Mon.
                
                # Check if this leave type is subject to sandwich policy (all or specific ones?)
                # Actually, Sandwich policy typically applies to certain leave types like CL, SL, EL.
                # If they want it on all, we can just do it.
                
                # Get normal working days from resource calendar
                resource_calendar = leave.employee_id.resource_calendar_id
                if not resource_calendar:
                    leave.sandwich_extra_days = 0.0
                    continue

                # Calendar days difference
                tz = leave.tz if hasattr(leave, 'tz') and leave.tz else 'UTC'
                start = leave.date_from.date()
                end = leave.date_to.date()
                
                if end > start:
                    total_days = (end - start).days + 1
                    
                    # Number of days without sandwich (Odoo's default calculation) usually
                    # is available in leave.number_of_days. However, number_of_days isn't fully computed
                    # at this stage if we depend on it. Wait, number_of_days is already computed
                    # by Odoo based on the resource calendar.
                    # We can't easily rely on number_of_days here because we might override it.
                    
                    # Let's calculate standard hours/days vs total calendar days.
                    # Actually, we can use resource calendar to find out how many days are weekends/holidays
                    # inside this period.
                    
                    # For a simple Sandwich policy: if total_days > resource_working_days + holidays between them
                    # Basically, extra_days = total_days - resource_working_days.
                    # Which is basically counting off-days that fall within the period.
                    
                    days_off = 0
                    current_date = start
                    while current_date <= end:
                        # check if current_date is a working day
                        import pytz
                        tz_obj = pytz.timezone(tz)
                        start_dt = tz_obj.localize(fields.Datetime.from_string(f"{current_date} 00:00:00")).astimezone(pytz.UTC)
                        end_dt = tz_obj.localize(fields.Datetime.from_string(f"{current_date} 23:59:59")).astimezone(pytz.UTC)
                        
                        intervals = resource_calendar._work_intervals_batch(start_dt, end_dt)
                        is_working_day = bool(intervals[False])
                        
                        # also check against hr.holiday.calendar
                        # If there's a holiday, it might be counted as off
                        holiday = self.env['hr.holiday.calendar'].search([
                            ('date', '=', current_date)
                        ], limit=1)
                        
                        if not is_working_day or holiday:
                            days_off += 1
                            
                        current_date += timedelta(days=1)
                        
                    extra_days = days_off
            leave.sandwich_extra_days = extra_days

    # Odoo 17/18 calculates duration in _compute_number_of_days. We need to add our sandwich days to it.
    @api.depends('sandwich_extra_days')
    def _compute_number_of_days(self):
        super(HrLeave, self)._compute_number_of_days()
        for leave in self:
            # Add sandwich days to the total number of days
            if leave.sandwich_extra_days:
                leave.number_of_days += leave.sandwich_extra_days
