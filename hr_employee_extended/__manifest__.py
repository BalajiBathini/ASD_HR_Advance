# -*- coding: utf-8 -*-
{
    
    "name": "Human Resources Employees Management System Extended Module",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    'sequence': 1,
    "author": "Balaji Bathini",
    'license': 'LGPL-3',    
    'website': 'https://github.com/BalajiBathini',
    "installable": True,
    "application": True,
    "summary": "Human Resources Employees Management System Extended Module",
    "depends": ["hr", "hr_recruitment",
                'hr_attendance', 'hr_holidays', 'hr_contract','hr_org_chart', 'payroll'


                ],
    "data": [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        # 'views/hr_contract_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_timeoff_allocation_views.xml',
        'views/hr_timeoff_rename_inherit.xml',
        # 'views/hr_payslip_views.xml',
        # 'views/playslip_report_modifications.xml',
    ],
    
    
}
