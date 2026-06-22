# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrSalaryDecreaseWizard(models.TransientModel):
    _name = 'hr.contract.salary.decrease.wizard'
    _description = 'Salary Decrease Confirmation Wizard'

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.company_id.currency_id')
    
    previous_ctc = fields.Monetary(string='Previous CTC', currency_field='currency_id')
    current_ctc = fields.Monetary(string='New CTC', currency_field='currency_id')
    amount_change = fields.Monetary(string='Decrease Amount', currency_field='currency_id')
    percentage_change = fields.Float(string='Decrease Percentage')

    def action_proceed(self):
        self.ensure_one()
        # Find the latest revision
        revisions = self.contract_id.revision_ids
        if revisions:
            latest_revision = revisions[0]
            latest_revision.current_ctc = self.current_ctc
            latest_revision.amount_change = self.amount_change
            latest_revision.percentage_change = self.percentage_change
            latest_revision.revision_type = 'decrease'
            
            # format the reason
            comment = "\nSalary revised from \u20B9{:,} to \u20B9{:,}.\nCTC decreased by \u20B9{:,} ({:.2f}% decrease).".format(
                int(self.previous_ctc), int(self.current_ctc), int(self.amount_change), self.percentage_change
            )
            latest_revision.reason = (latest_revision.reason or '') + comment
            
        # Set contract status for manager approval
        self.contract_id.salary_status = 'pending'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
