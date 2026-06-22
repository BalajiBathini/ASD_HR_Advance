from odoo import models, fields

class HrStateSalaryPolicy(models.Model):
    _name = 'hr.state.salary.policy'
    _description = 'State Salary Policy'

    name = fields.Char(string='Policy Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    country_id = fields.Many2one('res.country', string='Country', required=True, default=lambda self: self.env.company.country_id.id)
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    min_ctc = fields.Monetary(string='Minimum CTC', required=True, help="Minimum annual CTC required for this state.")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id)
    active = fields.Boolean(string='Active', default=True)
