# -*- coding: utf-8 -*-
{
    'name': 'Employee Profile DOCX',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Generate Employee Profile DOCX from Employee Record',
    'description': """
        Generates a formatted DOCX employee profile document from the employee form view.
        Includes personal details, qualification, experience, family/emergency contacts,
        and interview/joining information as per Company Template.
    """,
    'author': 'Balaji Bathini',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/employee_profile_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
