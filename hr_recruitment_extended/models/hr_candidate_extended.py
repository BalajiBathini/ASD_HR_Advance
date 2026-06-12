from email.policy import default

from odoo import fields, models, api
from odoo.tools.translate import _
from datetime import date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class HrCandidate(models.Model):
    _inherit = 'hr.candidate'

    # Copy all fields from hr.applicant model
    document_attachment_ids = fields.Many2many('ir.attachment', string="Document Attachments")
    education_ids = fields.One2many('applicant.education', 'candidate_id', string='Education Details')
    document_ids = fields.One2many('applicant.document', 'candidate_id', string='Document Details')
    employment_ids = fields.One2many('applicant.employment', 'candidate_id', string='Employment History')
    
    short_intro = fields.Text(string="Short Introduction")
    father_name = fields.Char(string="Father's Name")
    mother_name = fields.Char(string="Mother's Name")
    dob = fields.Date(string="Date of Birth")
    age = fields.Integer(
        string='Age',
        compute='_compute_age',
        inverse='_inverse_age',
        store=True,
        help="Candidate age computed from date of birth or can be set manually"
    )
    marital_status = fields.Selection([('yes', 'Yes'), ('no', 'No')] ,default="no", string="Marital Status")
    spouse_name = fields.Char(string="Spouse Name")
    mobile_no = fields.Char(string="Mobile No.")
    emergency_contact_no = fields.Char(string="Emergency Contact No.")
    emergency_contact_name = fields.Char(string="Emergency Contact Name")
    emergency_contact_relation = fields.Char(string="Emergency Contact Relation")
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-')
    ], string="Blood Group")
    medical_disability = fields.Text(string="Any Medical Disability")
    permanent_address = fields.Text(string="Permanent Address")
    present_address = fields.Text(string="Present Address")
    salary_expected = fields.Monetary(string="Expected Salary", currency_field='ctc_currency_id')
    is_negotiable = fields.Boolean(string="Is Expected Salary Negotiable")
    total_experience = fields.Char(string="Total Experience")
    notice_period = fields.Char(string="Notice Period")
    present_salary = fields.Monetary(string="Present Salary", currency_field='ctc_currency_id')
    interview_date = fields.Date(string="Date of Interview")
    mail_id = fields.Char(string="Mail Id")
    promotion_taken = fields.Boolean(string="Any Promotion Taken (Last 2 Years)")
    promoted_designation = fields.Char(string="Promoted Designation")
    special_increment = fields.Boolean(string="Any Special Increment (Last 12 Months)")
    increment_amount = fields.Monetary(string="Increment Amount / Annual", currency_field='ctc_currency_id')
    referred_by = fields.Char(string="Referred By")
    ctc_currency_id = fields.Many2one('res.currency', string='CTC Currency')
    ctc = fields.Monetary(string='CTC', currency_field='ctc_currency_id')
    destination = fields.Char(string='Destination')
    grade = fields.Char(string='Grade')
    other_skills = fields.Text(string="Other Skills")
    caste_id = fields.Many2one('applicant.caste', string='Caste')

    @api.depends('dob')
    def _compute_age(self):
        """Compute candidate age from date of birth."""
        today = date.today()
        for candidate in self:
            if candidate.dob:
                delta = relativedelta(today, candidate.dob)
                candidate.age = delta.years
            else:
                # Keep existing age if no dob (allows manual entry)
                if not candidate.age:
                    candidate.age = 0

    def _inverse_age(self):
        """Allow manual age entry without requiring dob."""
        # This inverse method allows the age to be set manually
        # When age is set manually, we don't modify dob
        pass

    def _get_employee_create_vals(self):
        vals = super(HrCandidate, self)._get_employee_create_vals()
        
        blood_map = {
            'A+': 'a_pos', 'A-': 'a_neg',
            'B+': 'b_pos', 'B-': 'b_neg',
            'AB+': 'ab_pos', 'AB-': 'ab_neg',
            'O+': 'o_pos', 'O-': 'o_neg'
        }
        
        marital_map = {
            'yes': 'married',
            'no': 'single'
        }
        
        vals.update({
            'father_name': self.father_name,
            'mother_name': self.mother_name,
            'birthday': self.dob,
            'marital': marital_map.get(self.marital_status) if self.marital_status else False,
            'spouse_complete_name': self.spouse_name,
            'emergency_contact': self.emergency_contact_name,
            'emergency_phone': self.emergency_contact_no,
        })
        
        if self.blood_group in blood_map:
            vals['blood_group'] = blood_map[self.blood_group]
            
        return vals

    def create_employee_from_candidate(self):
        self.ensure_one()
        return {
            'name': _('Create Employee & Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'applicant.employee.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'hr.candidate',
                'active_id': self.id,
            }
        }


class Applicant(models.Model):
    _inherit = 'hr.applicant'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to sync data from hr.candidate after applicant creation."""
        applicants = super(Applicant, self).create(vals_list)
        for applicant in applicants:
            if applicant.candidate_id:
                self._sync_candidate_data(applicant)
        return applicants
    
    def _sync_candidate_data(self, applicant):
        """Sync data from candidate to applicant, excluding skills as they are related."""
        candidate = applicant.candidate_id
        scalar_fields = {
            'partner_name': candidate.partner_name,
            'email_from': candidate.email_from,
            'partner_phone': candidate.partner_phone,
            'linkedin_profile': candidate.linkedin_profile,
            'short_intro': candidate.short_intro,
            'father_name': candidate.father_name,
            'mother_name': candidate.mother_name,
            'dob': candidate.dob,
            'age': candidate.age,
            'marital_status': candidate.marital_status,
            'spouse_name': candidate.spouse_name,
            'mobile_no': candidate.mobile_no,
            'emergency_contact_no': candidate.emergency_contact_no,
            'emergency_contact_name': candidate.emergency_contact_name,
            'emergency_contact_relation': candidate.emergency_contact_relation,
            'blood_group': candidate.blood_group,
            'medical_disability': candidate.medical_disability,
            'permanent_address': candidate.permanent_address,
            'present_address': candidate.present_address,
            'salary_expected': candidate.salary_expected,
            'is_negotiable': candidate.is_negotiable,
            'total_experience': candidate.total_experience,
            'notice_period': candidate.notice_period,
            'present_salary': candidate.present_salary,
            'interview_date': candidate.interview_date,
            'mail_id': candidate.mail_id,
            'promotion_taken': candidate.promotion_taken,
            'promoted_designation': candidate.promoted_designation,
            'special_increment': candidate.special_increment,
            'increment_amount': candidate.increment_amount,
            'referred_by': candidate.referred_by,
            'ctc_currency_id': candidate.ctc_currency_id.id if candidate.ctc_currency_id else False,
            'ctc': candidate.ctc,
            'destination': candidate.destination,
            'grade': candidate.grade,
            'other_skills': candidate.other_skills,
            'caste_id': candidate.caste_id.id if candidate.caste_id else False,
        }
        
        # Filter out None values to avoid errors
        filtered_fields = {k: v for k, v in scalar_fields.items() if hasattr(applicant, k)}
        
        # Link attachments
        if candidate.document_attachment_ids:
            filtered_fields['document_attachment_ids'] = [(6, 0, candidate.document_attachment_ids.ids)]
        
        # Apply all valid fields
        applicant.write(filtered_fields)
        
        # Sync one2many fields (excluding candidate_skill_ids as it’s related)
        # First remove existing records to avoid duplicates
        applicant.education_ids.unlink()
        applicant.document_ids.unlink()
        applicant.employment_ids.unlink()
        # Changed: Do not unlink candidate_skill_ids as it’s a related field; leave it to the candidate

        # Sync employment history
        for emp in candidate.employment_ids:
            emp_vals = {
                'applicant_id': applicant.id,
                'candidate_id': candidate.id,
                'employment_type_id': emp.employment_type_id.id if emp.employment_type_id else False,
                'company': emp.company,
                'location': emp.location,
                'duration_from': emp.duration_from,
                'duration_to': emp.duration_to,
                'designation': emp.designation,
                'reporting_officer': emp.reporting_officer,
                'years_of_experience': emp.years_of_experience,
                'leaving_reason': emp.leaving_reason,
                'previous_salary': emp.previous_salary,
            }
            new_emp = applicant.env['applicant.employment'].sudo().create(emp_vals)
            if emp.attachment_ids:
                new_emp.write({'attachment_ids': [(6, 0, emp.attachment_ids.ids)]})

        # Sync education details
        for edu in candidate.education_ids:
            edu_vals = {
                'applicant_id': applicant.id,
                'candidate_id': candidate.id,
                'exam_passed': edu.exam_passed,
                'subject': edu.subject,
                'specialization': edu.specialization,
                'institution': edu.institution,
                'marks_obtained': edu.marks_obtained,
                'year_of_passing': edu.year_of_passing,
                'study_type': edu.study_type,
                'achievements': edu.achievements,
            }
            new_edu = applicant.env['applicant.education'].sudo().create(edu_vals)
            if edu.attachment_ids:
                new_edu.write({'attachment_ids': [(6, 0, edu.attachment_ids.ids)]})

        # Sync document details
        for doc in candidate.document_ids:
            doc_vals = {
                'applicant_id': applicant.id,
                'candidate_id': candidate.id,
                'document_type': doc.document_type,
                'name_on_document': doc.name_on_document,
                'document_no': doc.document_no,
                'valid_from': doc.valid_from,
                'valid_to': doc.valid_to,
            }
            new_doc = applicant.env['applicant.document'].sudo().create(doc_vals)
            if doc.attachment_ids:
                new_doc.write({'attachment_ids': [(6, 0, doc.attachment_ids.ids)]})

