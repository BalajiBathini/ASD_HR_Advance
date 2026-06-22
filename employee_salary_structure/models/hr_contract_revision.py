# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrContractStructureRevision(models.Model):
    _name = 'hr.contract.structure.revision'
    _description = 'Contract Structure Revision'
    _order = 'revision_date desc, id desc'

    name = fields.Char(string='Revision Name', required=True, readonly=True)
    reason = fields.Text(string='Reason for Change', required=True)
    revision_date = fields.Datetime(string='Revision Date', default=fields.Datetime.now, required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', ondelete='cascade', required=True)
    
    currency_id = fields.Many2one('res.currency', related='contract_id.company_id.currency_id')
    previous_ctc = fields.Monetary(string='Previous CTC', currency_field='currency_id')
    current_ctc = fields.Monetary(string='Current CTC', currency_field='currency_id')
    amount_change = fields.Monetary(string='Amount Change', currency_field='currency_id')
    percentage_change = fields.Float(string='Percentage Change')
    revision_type = fields.Selection([
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
        ('unchanged', 'Unchanged')
    ], string='Revision Type')
