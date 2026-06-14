{
    'name': 'ASD HR Advance Attendance Roster',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Advanced attendance roster, weekly off management, and payroll integration',
    'sequence': 1,
    'author': 'Balaji Bathini',
    'license': 'LGPL-3',
    'depends': [
        'hr_attendance_extended',
        'payroll',
        'hr_holidays',
        'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_shift_views.xml',
        'views/attendance_weekoff_plan_views.xml',
        'views/attendance_monthly_sheet_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payslip_views.xml',
        'views/new_attendance_views.xml',
        'views/menus.xml',
        'views/reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
