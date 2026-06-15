from odoo import models, fields

class HrHolidayCalendar(models.Model):
    _name = 'hr.holiday.calendar'
    _description = 'Holiday Calendar'

    name = fields.Char("Holiday Name", required=True)
    date = fields.Date("Date", required=True)
    state_id = fields.Many2one('res.country.state', "State", help="Leave empty if applicable to all states")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('date_state_uniq', 'unique(date, state_id, company_id)', 'Holiday on this date for this state already exists!')
    ]
