# -*- coding: utf-8 -*-
{
    'name': 'Employee Self Service (Owl)',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Standalone Owl SPA for employee self service via portal',
    'description': """
    Employee Self Service - Standalone Owl App
    ==========================================

    A standalone Single Page Application (SPA) built with Owl framework
    for Odoo 17, allowing portal users to manage:

    - Attendance check-in/check-out
    - Expense reports
    - Contract information
    - Time-off requests

    Designed for employees who only have portal access (no backend access).
    """,
    'author': 'Diki',
    'website': 'https://github.com/d-q/odoo_addons',
    'maintainers': ['d-q'],
    'depends': ['web', 'portal', 'hr_attendance', 'hr_expense', 'hr_contract', 'hr_holidays'],
    'data': [
        'views/standalone_app.xml',
    ],
    'assets': {
        'owl_self_service.assets_standalone_app': [
            ('include', 'web.assets_frontend'),
            'web/static/src/libs/fontawesome/css/font-awesome.css',
            'web/static/src/scss/fontawesome_overridden.scss',
            'owl_self_service/static/src/standalone_app/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
