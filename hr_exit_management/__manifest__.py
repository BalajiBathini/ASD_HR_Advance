# -*- coding: utf-8 -*-
{
    'name': 'HR Exit & Offboarding Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'sequence': 1,
    'summary': 'End-to-end employee exit: resignation, clearance, F&F settlement, relieving letter',
    'description': """
HR Exit & Offboarding Management
=================================
Full custom module for Odoo 18 covering:
- Exit Request (resignation, last working day, reason)
- Approval Workflow (Draft -> Manager Accepted -> HR Accepted -> Clearance -> Done)
- Clearance Checklist (IT / Finance / Admin / HR)
- Asset Return Check (linked to hr.asset)
- F&F Computation (leave encashment, gratuity, notice deduction, net payable)
- Exit Interview
- Relieving Letter (auto-generated PDF)
- Employee Archive (archive, not delete)
""",
    'author': 'Balaji Bathini',
    'depends': ['hr', 'payroll', 'mail'],
    'data': [
        'security/hr_exit_security.xml',
        'security/ir.model.access.csv',
        'data/hr_exit_sequence.xml',
        'data/clearance_checklist_data.xml',
        'views/hr_exit_views.xml',
        'views/hr_exit_clearance_views.xml',
        'views/hr_exit_fnf_views.xml',
        'views/hr_exit_interview_views.xml',
        'views/hr_exit_menus.xml',
        'reports/hr_exit_relieving_letter.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
