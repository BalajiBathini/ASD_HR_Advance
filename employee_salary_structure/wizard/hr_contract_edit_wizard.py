# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrContractEditWizard(models.TransientModel):
    _name = 'hr.contract.structure.edit.wizard'
    _description = 'Contract Structure Edit Wizard'

    reason = fields.Text(string='Reason for Change', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)

    def action_apply(self):
        self.ensure_one()
        # Find latest revision to generate the next increment (R1, R2, etc.)
        revisions = self.contract_id.revision_ids
        next_number = len(revisions) + 1
        increment_name = f'R{next_number}'

        # Create the revision record
        self.env['hr.contract.structure.revision'].create({
            'name': increment_name,
            'reason': self.reason,
            'contract_id': self.contract_id.id,
            'previous_ctc': self.contract_id.annual_ctc,
        })

        # Set contract to editing
        self.contract_id.salary_status = 'editing'

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
