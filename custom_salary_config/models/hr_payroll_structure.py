from odoo import models, fields

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    custom_component_ids = fields.One2many('salary.component', 'structure_id', string='Salary Components Config')
