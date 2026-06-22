# -*- coding: utf-8 -*-
{
    'name': 'Employee Salary Structure',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Contracts',
    'sequence': 1,
    'author': 'Balaji Bathini',
    'license': 'LGPL-3',
    'summary': 'Individual employee salary management',
    'description': """
        Employee Salary Structure module.
        Extends employee contracts with custom isolated salary structures.
    """,
    'depends': ['hr_contract', 'custom_salary_config'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/hr_salary_decrease_wizard_views.xml',
        'wizard/hr_percentage_increase_wizard_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_contract_revision_views.xml',
        'views/hr_state_salary_policy_views.xml',
        'data/hr_salary_rules_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
