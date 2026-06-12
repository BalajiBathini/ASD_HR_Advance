# -*- coding: utf-8 -*-
{
    
    "name": "Recruitment Modification",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    'sequence': 1,
    "author": "Balaji Bathini",
    'license': 'LGPL-3',    
    'website': '',
    "installable": True,
    "application": True,
    "summary": "Custom modification in recruitment module",
    "depends": ["hr", "hr_recruitment", "mail", 'website', 'website_hr_recruitment', 'hr_recruitment_survey', 'hr_recruitment_skills', 'hr_skills'],
    "data": [
        'data/mail_template.xml',
        "data/hr_recruitment_data.xml",
        "security/ir.model.access.csv",
        "security/recruitment_security.xml",
        "views/cft_approval_views.xml",
        "views/cft_members_views.xml",
        "views/hr_job_views_extended.xml",
        "views/hr_recruitment_extended_view.xml",
        "views/website_hr_recruitment_modify.xml",
        'views/hr_candidate_extended_view.xml',
        'wizard/employee_contract_wizard_views.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
                    'hr_recruitment_extended/static/src/scss/website_hr_recruitment.scss',
                    'hr_recruitment_extended/static/src/css/custom.css',
                    'hr_recruitment_extended/static/src/css/web_form.css',
                ],
        'web.assets_frontend': [
                '/hr_recruitment_extended/static/src/js/application_form.js',
                # '/hr_recruitment_extended/static/src/js/js_skills.js',
                # '/hr_recruitment_extended/static/src/js/recruitment_form.js',
            ],
    },
    
}
