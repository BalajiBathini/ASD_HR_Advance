# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrContractPercentageIncreaseWizard(models.TransientModel):
    _name = 'hr.contract.percentage.increase.wizard'
    _description = 'Percentage Increase Wizard'

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.company_id.currency_id')
    
    current_ctc = fields.Monetary(string='Current CTC', related='contract_id.annual_ctc')
    percentage_increase = fields.Float(string='Increase Percentage (%)', required=True)
    new_ctc = fields.Monetary(string='New CTC', compute='_compute_new_ctc', currency_field='currency_id')
    reason = fields.Text(string='Reason for Increase', required=True)

    @api.depends('current_ctc', 'percentage_increase')
    def _compute_new_ctc(self):
        for rec in self:
            rec.new_ctc = rec.current_ctc * (1 + rec.percentage_increase / 100.0)

    def action_apply(self):
        self.ensure_one()
        if self.percentage_increase <= 0:
            return
        
        previous_ctc = self.current_ctc
        new_annual_ctc = self.new_ctc
        amount_change = new_annual_ctc - previous_ctc

        # Create revision
        revisions = self.contract_id.revision_ids
        next_number = len(revisions) + 1
        increment_name = f'R{next_number}'

        comment = "\nSalary revised from \u20B9{:,} to \u20B9{:,}.\nCTC increased by \u20B9{:,} ({:.2f}% increase). Reason: {}".format(
            int(previous_ctc), int(new_annual_ctc), int(amount_change), self.percentage_increase, self.reason
        )

        self.env['hr.contract.structure.revision'].create({
            'name': increment_name,
            'reason': comment,
            'contract_id': self.contract_id.id,
            'previous_ctc': previous_ctc,
            'current_ctc': new_annual_ctc,
            'amount_change': amount_change,
            'percentage_change': self.percentage_increase,
            'revision_type': 'increase'
        })

        self.contract_id.annual_ctc = new_annual_ctc
        
        # Sent for approval
        self.contract_id.salary_status = 'pending'

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
