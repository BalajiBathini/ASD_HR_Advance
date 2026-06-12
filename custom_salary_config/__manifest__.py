# -*- coding: utf-8 -*-
{
    'name': 'Custom Salary Configuration',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'sequence': 1,
    'author': 'Balaji Bathini',
    'summary': 'Centralized salary structure and component configuration',
    'description': """
        Custom Salary Configuration module to manage HR-friendly payroll rules.
        Replaces Python-code requirements for payroll structures.
    """,
    'depends': ['base', 'hr', 'payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/salary_structure_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
