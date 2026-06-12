from odoo import http
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment
from odoo.http import request
import base64
import re

class WebsiteHrRecruitmentExtended(WebsiteHrRecruitment):
    def extract_data(self, model, values):
        """Extract and save data for hr.candidate and hr.applicant from form submission."""
        values_copy = values.copy()  # Create a copy of the form values to avoid modifying the original
        data = super(WebsiteHrRecruitmentExtended, self).extract_data(model, values)  # Call parent method to get initial data

        if model.sudo().model == 'hr.applicant' and 'candidate_id' in data['record']:
            candidate = request.env['hr.candidate'].sudo().browse(data['record']['candidate_id'])  # Fetch candidate record
            applicant = request.env['hr.applicant'].sudo().browse(data['record'].get('id'))  # Fetch applicant record if exists

            # Process scalar fields for candidate
            candidate_fields = request.env['hr.candidate']._fields  # Get all fields of hr.candidate model
            candidate_vals = {}  # Dictionary to store scalar field updates
            for field, value in values_copy.items():
                if field in candidate_fields and field not in ['document_attachment_ids', 'education_ids', 'document_ids', 'employment_ids', 'candidate_skill_ids']:
                    field_type = candidate_fields[field].type  # Get field type for proper casting
                    if field_type == 'boolean':
                        candidate_vals[field] = True if value == 'on' else False  # Handle checkbox fields
                    elif field_type in ['float', 'monetary']:
                        candidate_vals[field] = float(value) if value and value.strip() else 0.0  # Convert to float
                    elif field_type == 'integer':
                        candidate_vals[field] = int(value) if value and value.strip() else 0  # Convert to integer
                    elif field_type == 'many2one':
                        candidate_vals[field] = int(value) if value and value.strip() else False  # Convert to ID
                    else:
                        candidate_vals[field] = value  # Use value as is for char, text, etc.
            if candidate_vals:
                candidate.sudo().write(candidate_vals)  # Update candidate with scalar field values

            # Handle document_attachment_ids (Many2many field)
            if request.httprequest.files and 'document_attachment_ids' in request.httprequest.files:
                attachment_ids = []  # List to store new attachment IDs
                files = request.httprequest.files.getlist('document_attachment_ids')  # Get uploaded files
                for file in files:
                    if file and file.filename:
                        attachment_data = {
                            'name': file.filename,  # Set attachment name
                            'datas': base64.b64encode(file.read()),  # Encode file content
                        }
                        new_attachment = request.env['ir.attachment'].sudo().create(attachment_data)  # Create attachment
                        attachment_ids.append(new_attachment.id)  # Add ID to list
                if attachment_ids:
                    candidate.sudo().write({'document_attachment_ids': [(6, 0, attachment_ids)]})  # Replace attachments
                    if applicant.exists():
                        applicant.sudo().write({'document_attachment_ids': [(6, 0, attachment_ids)]})  # Sync to applicant

            # Define One2many fields and their corresponding models
            one2many_fields = {
                'education_ids': 'applicant.education',  # Education details
                'document_ids': 'applicant.document',  # Document details
                'employment_ids': 'applicant.employment',  # Employment history
                'candidate_skill_ids': 'hr.candidate.skill',  # Skills data
            }
            one2many_data = {field: {} for field in one2many_fields}  # Dictionary to store parsed One2many data
            one2many_attachments = {field: {} for field in one2many_fields}  # Dictionary to store One2many attachments
            pattern = re.compile(r'(\w+)\[(\d+)\]\[(\w+)\]')  # Regex to parse field names like candidate_skill_ids[0][skill_id]

            # Parse form data for One2many fields
            for key, value in values_copy.items():
                match = pattern.match(key)  # Match field name pattern
                if match:
                    field_name, index, sub_field = match.groups()  # Extract field name, index, and sub-field
                    index = int(index)  # Convert index to integer
                    if field_name in one2many_fields:
                        if index not in one2many_data[field_name]:
                            one2many_data[field_name][index] = {}  # Initialize sub-dictionary for this index
                        one2many_data[field_name][index][sub_field] = value  # Store value

            # Parse file attachments for One2many fields
            if request.httprequest.files:
                for key in request.httprequest.files:
                    match = pattern.match(key)  # Match attachment field name
                    if match and match.group(1) in one2many_fields:
                        field_name, index, sub_field = match.groups()  # Extract components
                        index = int(index)  # Convert index to integer
                        if sub_field == 'attachment_ids':
                            if index not in one2many_attachments[field_name]:
                                one2many_attachments[field_name][index] = []  # Initialize attachment list
                            files = request.httprequest.files.getlist(key)  # Get list of files
                            for file in files:
                                if file and file.filename:
                                    one2many_attachments[field_name][index].append(file)  # Add file to list

            # Process each One2many field
            for field_name, model_name in one2many_fields.items():
                model = request.env[model_name].sudo()  # Get model object with sudo access
                model_fields = model._fields  # Get fields of the model

                # Clear existing records to avoid duplicates
                if field_name == 'candidate_skill_ids':
                    candidate.candidate_skill_ids.sudo().unlink()  # Remove existing skills for candidate
                else:
                    getattr(candidate, field_name).sudo().unlink()  # Remove existing records for other fields

                # Also clear applicant records to ensure clean slate before creating new ones
                if applicant.exists() and hasattr(applicant, field_name):
                    getattr(applicant, field_name).sudo().unlink()  # Remove existing applicant records

                # Create new records
                for index, record_data in one2many_data[field_name].items():
                    # Initialize record_vals with only fields that exist in the model
                    record_vals = {}
                    if 'candidate_id' in model_fields:
                        record_vals['candidate_id'] = candidate.id  # Link to candidate if field exists

                    # Add sub-fields from form data
                    for sub_field, value in record_data.items():
                        if sub_field in model_fields and sub_field != 'attachment_ids':
                            field_type = model_fields[sub_field].type  # Get sub-field type
                            if field_type == 'boolean':
                                record_vals[sub_field] = True if value == 'on' else False  # Handle boolean
                            elif field_type in ['float', 'monetary']:
                                record_vals[sub_field] = float(value) if value and value.strip() else 0.0  # Handle float/monetary
                            elif field_type == 'integer':
                                record_vals[sub_field] = int(value) if value and value.strip() else 0  # Handle integer
                            elif field_type == 'many2one':
                                record_vals[sub_field] = int(value) if value and value.strip() else False  # Handle Many2one
                            elif field_type == 'selection':
                                record_vals[sub_field] = value if value and value.strip() else False  # Handle selection
                            else:
                                record_vals[sub_field] = value  # Handle char/text

                    # Ensure required fields are present before creating
                    required_fields = [f for f in model_fields if model_fields[f].required]
                    if not all(record_vals.get(f) for f in required_fields):
                        continue  # Skip if required fields are missing

                    try:
                        # Create record for candidate
                        new_record = model.create(record_vals)  # Create new record
                        
                        # Handle attachments
                        if index in one2many_attachments[field_name]:
                            attachment_ids = []  # List for attachment IDs
                            for file in one2many_attachments[field_name][index]:
                                attachment_data = {
                                    'name': file.filename,  # Set attachment name
                                    'datas': base64.b64encode(file.read()),  # Encode file content
                                }
                                attachment = request.env['ir.attachment'].sudo().create(attachment_data)  # Create attachment
                                attachment_ids.append(attachment.id)  # Add ID to list
                            if attachment_ids:
                                new_record.write({'attachment_ids': [(6, 0, attachment_ids)]})  # Link attachments
                        
                        # Create same record for applicant if it exists
                        if applicant.exists() and hasattr(applicant, field_name) and 'applicant_id' in model_fields:
                            # Copy record values for applicant
                            applicant_record_vals = record_vals.copy()
                            applicant_record_vals['applicant_id'] = applicant.id  # Add applicant_id
                            if 'candidate_id' in model_fields:
                                applicant_record_vals['candidate_id'] = candidate.id  # Preserve candidate_id reference
                            
                            # Create applicant record
                            new_applicant_record = model.create(applicant_record_vals)
                            
                            # Copy attachments to applicant record if any
                            if attachment_ids:
                                new_applicant_record.write({'attachment_ids': [(6, 0, attachment_ids)]})
                                
                    except Exception as e:
                        print(f"Error creating {model_name} record: {e}")  # Log error for debugging
                        continue

            # Sync scalar field data to applicant if it exists - handle this separately
            if applicant.exists():
                # Only sync scalar fields, not one2many fields as we already handled those
                self._sync_scalar_fields(candidate, applicant)

        return data  # Return extracted data
    
    def _sync_scalar_fields(self, candidate, applicant):
        """Sync only scalar fields from candidate to applicant to avoid duplication."""
        scalar_fields = {
            'partner_name': candidate.partner_name,
            'email_from': candidate.email_from,
            'partner_phone': candidate.partner_phone,
            'linkedin_profile': candidate.linkedin_profile,
            'short_intro': candidate.short_intro,
            'father_name': candidate.father_name,
            'mother_name': candidate.mother_name,
            'dob': candidate.dob,
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
        }
        
        # Filter out None values to avoid errors
        filtered_fields = {k: v for k, v in scalar_fields.items() if hasattr(applicant, k)}
        
        # Apply all valid fields
        applicant.write(filtered_fields)

    @http.route('/website_hr_recruitment/get_skills_by_type', type='json', auth='public', website=True, csrf=False)
    def get_skills_by_type(self, **kw):
        """Fetch all skills and levels related to a given skill_type_id for public access."""
        try:
            # Extract skill_type_id from parameters
            skill_type_id = kw.get('skill_type_id')
            if not skill_type_id:
                return {'error': 'Missing skill_type_id parameter'}
            
            # Convert to integer if needed
            if isinstance(skill_type_id, str) and skill_type_id.isdigit():
                skill_type_id = int(skill_type_id)
            
            if not isinstance(skill_type_id, int):
                return {'error': 'Invalid skill type ID format'}

            # Fetch skills related to the skill_type_id
            skills = request.env['hr.skill'].sudo().search_read(
                domain=[('skill_type_id', '=', skill_type_id)],
                fields=['id', 'name']
            )

            # Fetch skill levels related to the skill_type_id
            levels = request.env['hr.skill.level'].sudo().search_read(
                domain=[('skill_type_id', '=', skill_type_id)],
                fields=['id', 'name'],
                order='level_progress ASC'
            )

            # Return skills and levels in a format suitable for the frontend
            return {
                'skills': [{'id': skill['id'], 'name': skill['name']} for skill in skills],
                'levels': [{'id': level['id'], 'name': level['name']} for level in levels],
                'error': None
            }
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.exception("Error in get_skills_by_type: %s", str(e))
            return {'error': f"Error fetching skills: {str(e)}"}