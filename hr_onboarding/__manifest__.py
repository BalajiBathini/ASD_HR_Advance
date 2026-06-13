{
    'name': 'HR Onboarding',
    'version': '18.0.1.0.0',
    'summary': 'Full Employee Onboarding Workflow — Day 0 to Day 30',
    'sequence': 1,
    'author': 'Balaji Bathini',
    'license': 'LGPL-3',
    'description': """
        Enterprise-grade employee onboarding module for Odoo 18 Community.
        Features:
        - Reusable onboarding templates with categorized tasks
        - Auto-creation of onboarding plan on employee joining
        - Task assignment with due date calculation from join date
        - Email notifications to responsible persons
        - Progress tracking with completion percentage
        - Kanban dashboard for manager view
        - Chatter / activity log on each onboarding plan
    """,


    'category': 'Human Resources',
    'depends': ['hr', 'hr_recruitment', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_onboarding_template_data.xml',
        'data/mail_template_data.xml',
        'views/hr_onboarding_template_views.xml',
        'views/hr_onboarding_views.xml',
        'views/hr_onboarding_task_views.xml',
        'views/hr_employee_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
