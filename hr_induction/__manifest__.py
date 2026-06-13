# -*- coding: utf-8 -*-
{
    
    "name": "Employee Induction Management System",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    'sequence': 1,
    "author": "Balaji Bathini",
    'license': 'LGPL-3',    
    'website': '',
    "installable": True,
    "application": True,
    "summary": "Employee Induction Management System",
    "depends": ['hr', "hr_recruitment", "mail", 'website', 'portal', 'hr_contract', 'hr_employee_extended'],
    "data": [
        "data/hr_induction_data.xml",
        "security/ir.model.access.csv",
        'views/hr_induction_views.xml',
        'views/hr_induction_portal_views.xml',
    ],
    
    
}
