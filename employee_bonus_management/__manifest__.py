# -*- coding: utf-8 -*-
{
    'name': 'Employee Bonus Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Manage bonuses and incentives',
    'description': """
        Manage employee bonuses and incentives.
        Includes a bulk wizard to apply bonuses across all or selected employees.
    """,
    'depends': ['hr', 'custom_salary_config', 'employee_salary_structure', 'salary_attachments', 'payroll'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_salary_rules.xml',
        'wizard/bulk_bonus_wizard_views.xml',
        'views/hr_bonus_views.xml',
        'views/hr_payslip_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
