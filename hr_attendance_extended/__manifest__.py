{
    'name': 'HR Attendance Extended',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Extended Attendance with Carry-Forward and Payroll',
    'description': """
        Manage employee attendance and payroll working-hours management.
        Calculates government standard monthly working hours, actual worked hours from attendance, 
        extra worked hours, remaining balance hours, and carry-forward hours.
    """,
    'author': 'Balaji Bathini',
    'sequence' : 1,
    'depends': ['hr_attendance', 'payroll', 'hr_employee_extended'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron.xml',
        'views/res_config_settings_views.xml',
        'views/attendance_batch_ledger_wizard_views.xml',
        'views/attendance_monthly_balance_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
