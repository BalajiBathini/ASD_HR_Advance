# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from markupsafe import Markup
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.translate import _


class Applicant(models.Model):
    _inherit = "hr.applicant"


    state_sequence = fields.Integer(
        string='Stage Sequence',
        compute='_compute_stage_sequence',
        store=True,
        help="The sequence number of the current stage."
    )
    is_last_stage = fields.Boolean(
        string='Is Last Stage',
        compute='_compute_is_last_stage',
        store=True,
        help="Indicates if the current stage is the final (hired) stage."
    )
    
    destination = fields.Char(string='Destination')
    grade = fields.Char(string='Grade')
    
    ctc_currency_id = fields.Many2one('res.currency', string='CTC Currency')
    ctc = fields.Monetary(
        string='CTC',
        currency_field='ctc_currency_id'
    )

    @api.depends('stage_id')
    def _compute_stage_sequence(self):
        """Compute the state_sequence based on the current stage's sequence."""
        for applicant in self:
            applicant.state_sequence = applicant.stage_id.sequence if applicant.stage_id else 0

    @api.depends('stage_id')
    def _compute_is_last_stage(self):
        """Compute is_last_stage based on whether the current stage is marked as hired."""
        for applicant in self:
            applicant.is_last_stage = applicant.stage_id.hired_stage if applicant.stage_id else False

    def action_move_to_next_stage(self):
        """Move the applicant to the next stage based on sequence."""
        self.ensure_one()
        next_stage = self.env['hr.recruitment.stage'].search([
            ('sequence', '>', self.state_sequence)
        ], order='sequence asc', limit=1)
        if next_stage:
            self.write({'stage_id': next_stage.id})
            # Update kanban_state based on the new stage's hired_stage
            self.kanban_state = 'done' if next_stage.hired_stage else 'normal'
    
    def action_move_to_previous_stage(self):
        """Move the applicant to the previous stage based on sequence."""
        self.ensure_one()
        if self.state_sequence <= 0:
            raise UserError("Cannot move back from the first stage.")
        
        previous_stage = self.env['hr.recruitment.stage'].search([
            ('sequence', '<', self.state_sequence)
        ], order='sequence desc', limit=1)
        
        if previous_stage:
            self.write({'stage_id': previous_stage.id})
            # Update kanban_state based on the new stage's hired_stage
            self.kanban_state = 'done' if previous_stage.hired_stage else 'normal'

    def write(self, vals):
        if 'stage_id' in vals:
            new_stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])
            if new_stage.name == 'Offer Letter Release':
                for applicant in self:
                    ctc_val = vals.get('ctc', applicant.ctc)
                    if not ctc_val or ctc_val <= 0.0:
                        raise ValidationError(_("Please enter CTC after negotiation before moving to Offer Letter Release."))
        return super(Applicant, self).write(vals)

    def create_employee_from_applicant(self):
        self.ensure_one()
        return {
            'name': _('Create Employee & Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'applicant.employee.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'hr.applicant',
                'active_id': self.id,
            }
        }