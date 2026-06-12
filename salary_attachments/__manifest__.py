# -*- coding: utf-8 -*-
{
    'name': 'Salary Attachments',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'sequence': 1,
    'author': 'Balaji Bathini',
    'license': 'LGPL-3',
    'summary': 'Manage employee deductions and additions',
    'description': """
        Manage employee loans, salary advances, and other deductions.
        Automatically process EMI deductions during payslip generation.
    """,
    'depends': ['hr', 'hr_contract', 'payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/salary_attachment_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
