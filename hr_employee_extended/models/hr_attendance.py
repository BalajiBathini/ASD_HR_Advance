# -*- coding: utf-8 -*-
from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    employee_code = fields.Char(
        string='Employee Code',
        related='employee_id.employee_code',
        store=True,
        readonly=True,
        help="Employee code from the employee record"
    )
