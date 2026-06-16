{
    'name': 'HR Appraisal KPI',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Custom Appraisal module with KRA/KPI based performance management',
'sequence': 1,
    'author': 'Balaji Bathini',
    'description': """
HR Appraisal KPI
================
Custom-built Appraisal module (since hr_appraisal is Odoo Enterprise only) with:
- Appraisal Creation (Manager/HR triggers appraisal)
- Self Assessment (employee self review)
- Manager Feedback (structured rating)
- Skills Review integration (hr.employee.skill)
- 360 Feedback (partial - peer/subordinate invites)
- Appraisal Templates (configurable questionnaire)
- KRA (Key Result Areas) with weightage
- KPI (Quantitative targets vs actuals) with achievement %
- Computed overall weighted rating
- Bell Curve Rating (Exceeds/Meets/Below/Far Below)
- Goal Carry Forward to next cycle
""",
    'depends': ['hr', 'hr_skills', 'mail'],
    'data': [
        'security/hr_appraisal_security.xml',
        'security/ir.model.access.csv',
        'data/hr_appraisal_data.xml',
        'views/hr_appraisal_views.xml',
        'views/hr_appraisal_kra_views.xml',
        'views/hr_appraisal_kpi_views.xml',
        'views/hr_appraisal_template_views.xml',
        'views/hr_appraisal_feedback_views.xml',
        'views/hr_appraisal_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
