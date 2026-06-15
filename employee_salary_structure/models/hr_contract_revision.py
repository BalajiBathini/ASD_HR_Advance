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
