from odoo import api, fields, models
from datetime import date
from dateutil.relativedelta import relativedelta
import uuid


class ApplicantCaste(models.Model):
    _name = 'applicant.caste'
    _description = 'Applicant Caste'

    name = fields.Char(string='Caste Name', required=True)


class ApplicantEducation(models.Model):
    _name = 'applicant.education'
    _description = 'Applicant Education Details'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete='cascade')
    candidate_id = fields.Many2one('hr.candidate', string='Candidate', ondelete='cascade')
    exam_passed = fields.Selection(
        [
            ('10th', '10th'),
            ('12th', '12th'),
            ('graduation', 'Graduation'),
            ('technical', 'Technical'),
            ('certification', 'Any other Certifications')
        ],
        string='Exam Passed',
        required=True
    )
    subject = fields.Char(string='Subject')
    specialization = fields.Char(string='Specialization')
    institution = fields.Char(string='School/College/University/Other')
    marks_obtained = fields.Float(string='Marks Obtained (%)')
    year_of_passing = fields.Integer(string='Year of Passing')
    study_type = fields.Selection(
    [('full_time', 'Full Time'), ('part_time', 'Part Time')],
        string='Full Time / Part Time'
    )
    achievements = fields.Text(string='Achievements')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

class EmploymentType(models.Model):
    _name = 'employment.type'
    _description = 'Employment Type'
    
    name = fields.Char(string='Name', required=True)
    
    
class ApplicantDocument(models.Model):
    _name = 'applicant.document'
    _description = 'Applicant Document Details'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete='cascade')
    candidate_id = fields.Many2one('hr.candidate', string='Candidate', ondelete='cascade')
    document_type = fields.Selection(
        [
            ('aadhar', 'Aadhaar Card'),
            ('pan', 'Pan Card'),
            ('election', 'Election Card'),
            ('passport', 'Passport'),
            ('birth_certificate', 'Birth Certificate'),
            ('bank_account', 'Bank Account'),
            ('photo', 'Passport Size Photo')
        ],
        string='Document Type',
        required=True
    )
    name_on_document = fields.Char(string='Name on Document')
    document_no = fields.Char(string='Document No')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    attachment_ids = fields.Many2many('ir.attachment', string='Document Attachment')



class ApplicantEmployment(models.Model):
    _name = 'applicant.employment'
    _description = 'Applicant Employment History'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', ondelete='cascade')
    candidate_id = fields.Many2one('hr.candidate', string='Candidate', ondelete='cascade')
    employment_type_id = fields.Many2one(
        'employment.type', 
        string='Details', 
        required=True
    )
    company = fields.Char(string='Company')
    location = fields.Char(string='Location')
    duration_from = fields.Date(string='Duration From')
    duration_to = fields.Date(string='Duration To')
    designation = fields.Char(string='Designation')
    reporting_officer = fields.Char(string='Reporting Officer')
    years_of_experience = fields.Float(string='No. of years of Exp.')
    leaving_reason = fields.Text(string='Reason for leaving')
    previous_salary = fields.Float(string='Previous Salary')
    attachment_ids = fields.Many2many('ir.attachment', string='Experience Certificate')


class Applicant(models.Model):
    _inherit = 'hr.applicant'

    # Image fields similar to hr.employee (avatar.mixin functionality)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    image_1024 = fields.Image("Image 1024", related="image_1920", max_width=1024, max_height=1024, store=True)
    image_512 = fields.Image("Image 512", related="image_1920", max_width=512, max_height=512, store=True)
    image_256 = fields.Image("Image 256", related="image_1920", max_width=256, max_height=256, store=True)
    image_128 = fields.Image("Image 128", related="image_1920", max_width=128, max_height=128, store=True)

    # Avatar fields (with fallback to default avatar)
    avatar_1920 = fields.Image("Avatar 1920", compute='_compute_avatar_1920', store=False)
    avatar_1024 = fields.Image("Avatar 1024", compute='_compute_avatar_1024', store=False)
    avatar_512 = fields.Image("Avatar 512", compute='_compute_avatar_512', store=False)
    avatar_256 = fields.Image("Avatar 256", compute='_compute_avatar_256', store=False)
    avatar_128 = fields.Image("Avatar 128", compute='_compute_avatar_128', store=False)

    def _compute_avatar(self, avatar_field, image_field):
        for record in self:
            avatar = record[image_field]
            if not avatar:
                avatar = record._get_default_avatar()
            record[avatar_field] = avatar

    def _compute_avatar_1920(self):
        self._compute_avatar('avatar_1920', 'image_1920')

    def _compute_avatar_1024(self):
        self._compute_avatar('avatar_1024', 'image_1024')

    def _compute_avatar_512(self):
        self._compute_avatar('avatar_512', 'image_512')

    def _compute_avatar_256(self):
        self._compute_avatar('avatar_256', 'image_256')

    def _compute_avatar_128(self):
        self._compute_avatar('avatar_128', 'image_128')

    def _get_default_avatar(self):
        """Return the default avatar for applicants without an image."""
        return False

    document_attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Document Attachments",
        help="Attach relevant documents to the applicant."
    )
    
    education_ids = fields.One2many('applicant.education', 'applicant_id', string='Education Details')
    document_ids = fields.One2many('applicant.document', 'applicant_id', string='Document Details')
    employment_ids = fields.One2many('applicant.employment', 'applicant_id', string='Employment History')
    
    short_intro = fields.Text(
        string="Short Introduction",
        help="A brief introduction about the applicant."
    )
    
    father_name = fields.Char(string="Father's Name")
    mother_name = fields.Char(string="Mother's Name")
    dob = fields.Date(string="Date of Birth")
    age = fields.Integer(
        string='Age',
        compute='_compute_age',
        inverse='_inverse_age',
        store=True,
        help="Applicant age computed from date of birth or can be set manually"
    )
    marital_status = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],default="no",
        string="Marital Status"
    )
    spouse_name = fields.Char(string="Spouse Name")
    mobile_no = fields.Char(string="Mobile No.")  # Separate from partner_mobile if needed
    emergency_contact_no = fields.Char(string="Emergency Contact No.")
    emergency_contact_name = fields.Char(string="Emergency Contact Name")
    emergency_contact_relation = fields.Char(string="Emergency Contact Relation")
    blood_group = fields.Selection(
        [
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-')
        ],
        string="Blood Group"
    )
    medical_disability = fields.Text(string="Any Medical Disability")
    permanent_address = fields.Text(string="Permanent Address")
    present_address = fields.Text(string="Present Address")
    salary_expected = fields.Monetary(
        string="Expected Salary",
        currency_field='ctc_currency_id'
    )
    is_negotiable = fields.Boolean(string="Is Expected Salary Negotiable")
    total_experience = fields.Char(string="Total Experience")  # e.g., "2 years 3 months"
    notice_period = fields.Char(string="Notice Period")  # e.g., "30 days"
    present_salary = fields.Monetary(
        string="Present Salary",
        currency_field='ctc_currency_id'
    )
    interview_date = fields.Date(string="Date of Interview")
    mail_id = fields.Char(string="Mail Id")  # Separate from email_from if needed
    promotion_taken = fields.Boolean(string="Any Promotion Taken (Last 2 Years)")
    promoted_designation = fields.Char(string="Promoted Designation")
    special_increment = fields.Boolean(string="Any Special Increment (Last 12 Months)")
    increment_amount = fields.Monetary(
        string="Increment Amount / Annual",
        currency_field='ctc_currency_id'
    )
    referred_by = fields.Char(string="Referred By")
    other_skills = fields.Text(string="Other Skills")
    caste_id = fields.Many2one('applicant.caste', string='Caste')

    @api.depends('dob')
    def _compute_age(self):
        """Compute applicant age from date of birth."""
        today = date.today()
        for applicant in self:
            if applicant.dob:
                delta = relativedelta(today, applicant.dob)
                applicant.age = delta.years
            else:
                # Keep existing age if no dob (allows manual entry)
                if not applicant.age:
                    applicant.age = 0

    def _inverse_age(self):
        """Allow manual age entry without requiring dob."""
        # This inverse method allows the age to be set manually
        # When age is set manually, we don't modify dob
        pass