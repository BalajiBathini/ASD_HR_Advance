{
    'name': 'HR Advance - Leave Management Extended',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Time Off',

    'sequence': 1,
    "author": "Balaji Bathini",
    'summary': 'Extended leave management features: Encashment, Sandwich Policy, Automations',
    'description': """
Extended Leave Management:
- Leave type configuration (Carry Forward, Encashable, Paid).
- Sandwich Policy implementation.
- Leave Encashment workflow.
- State-wise Holiday Calendar.
- Auto Leave Accruals.
- Comp Off Generation on Holidays/Weekends.
- OWL JS Leave Dashboard.
    """,

    'website': '',
    'depends': [
        'hr_holidays',
        'payroll',
        'hr_attendance',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/leave_cron.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_holiday_calendar_views.xml',
        'views/hr_leave_encashment_views.xml',
        'views/leave_dashboard_views.xml',
        'views/hr_leave_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_leave_extended/static/src/components/leave_dashboard/**/*',
            'hr_leave_extended/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
