/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.hrRecruitmentExtended = publicWidget.Widget.extend({
    selector: '#hr_recruitment_form',
    events: {
        'click #apply-btn': '_onClickApplyButton',
        "focusout #recruitment1": "_onFocusOutName",
        'focusout #recruitment2': '_onFocusOutMail',
        "focusout #recruitment3": "_onFocusOutPhone",
        'focusout #recruitment4': '_onFocusOutLinkedin',
        'change select[name="marital_status"]': '_onMaritalStatusChange',
        'click .add-employment-row': '_onAddEmploymentRow',
        'click .delete-employment-row': '_onDeleteEmploymentRow',
        'change input[name^="employment_ids"][name$="[duration_from]"]': '_calculateExperience',
        'change input[name^="employment_ids"][name$="[duration_to]"]': '_calculateExperience',
        'change select[name^="education_ids"][name$="[exam_passed]"]': '_validateEducationFields',
        'change select[name^="document_ids"][name$="[document_type]"]': '_setDocumentValidation',
        'input input[name="present_address"]': '_onSameAddressCheck',
        'change input[name="is_same_address"]': '_onSameAddressToggle',
        'click .delete-file': '_onFileDeleteClick',
        'change input[type="file"]': '_onFileChange',
        'change input[name="salary_expected"]': '_validateSalary',
        'change input[name="present_salary"]': '_validateSalary',
        'change input[type="file"]': '_validateFileSize',
        'click .add-skill-row': '_onAddSkillRow',
        'click .delete-skill-row': '_onDeleteSkillRow',
        'change select[name^="candidate_skill_ids"][name$="[skill_type_id]"]': '_onSkillTypeChange',
    },

    // Hide warning message for a field
    hideWarningMessage(targetEl, messageContainerId) {
        targetEl.classList.remove("border-warning");
        document.querySelector(messageContainerId)?.classList.add("d-none");
    },

    // Show warning message for a field
    showWarningMessage(targetEl, messageContainerId, message) {
        targetEl.classList.add("border-warning");
        document.querySelector(messageContainerId).textContent = message;
        document.querySelector(messageContainerId)?.classList.remove("d-none");
    },

    // Check for redundant name
    async _onFocusOutName(ev) {
        const field = "name";
        const messageContainerId = "#warning-message";
        await this.checkRedundant(ev.currentTarget, field, messageContainerId);
    },

    // Check for redundant email
    async _onFocusOutMail(ev) {
        const field = "email";
        const messageContainerId = "#warning-message";
        await this.checkRedundant(ev.currentTarget, field, messageContainerId);
    },

    // Check for redundant phone
    async _onFocusOutPhone(ev) {
        const field = "phone";
        const messageContainerId = "#warning-message";
        await this.checkRedundant(ev.currentTarget, field, messageContainerId);
    },

    // Validate LinkedIn URL and check redundancy
    async _onFocusOutLinkedin(ev) {
        const targetEl = ev.currentTarget;
        const linkedin = targetEl.value;
        const field = "linkedin";
        const messageContainerId = "#linkedin-message";
        const linkedin_regex = /^(https?:\/\/)?([\w\.]*)linkedin\.com\/in\/(.*?)(\/.*)?$/;
        let hasWarningMessage = false;

        if (!linkedin_regex.test(linkedin) && linkedin !== "") {
            const message = _t("The profile that you gave us doesn't seem like a LinkedIn profile");
            this.showWarningMessage(targetEl, "#linkedin-message", message);
            hasWarningMessage = true;
        } else {
            this.hideWarningMessage(targetEl, "#linkedin-message");
        }

        if (linkedin && !linkedin.includes('linkedin.com/in/')) {
            this.showWarningMessage(targetEl, "#linkedin-message",
                _t("Please enter a complete LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)"));
            hasWarningMessage = true;
        }

        await this.checkRedundant(targetEl, field, messageContainerId, hasWarningMessage);
    },

    // Check for redundant field values via RPC
    async checkRedundant(targetEl, field, messageContainerId, keepPreviousWarningMessage = false) {
        const value = targetEl.value;
        if (!value) {
            this.hideWarningMessage(targetEl, messageContainerId);
            return;
        }
        const job_id = document.querySelector("#recruitment7").value;
        const data = await rpc("/website_hr_recruitment/check_recent_application", {
            field: field,
            value: value,
            job_id: job_id,
        });

        if (data.message) {
            this.showWarningMessage(targetEl, messageContainerId, data.message);
        } else if (!keepPreviousWarningMessage) {
            this.hideWarningMessage(targetEl, messageContainerId);
        }
    },

    // Handle form submission
    _onClickApplyButton(ev) {
        const linkedinProfileEl = document.querySelector("#recruitment4");
        const resumeEl = document.querySelector("#recruitment6");

        const isLinkedinEmpty = !linkedinProfileEl || linkedinProfileEl.value.trim() === "";
        const isResumeEmpty = !resumeEl || !resumeEl.files.length;
        if (isLinkedinEmpty && isResumeEmpty) {
            linkedinProfileEl?.setAttribute("required", true);
            resumeEl?.setAttribute("required", true);
        } else {
            linkedinProfileEl?.removeAttribute("required");
            resumeEl?.removeAttribute("required");
        }

        if (!this._validateForm()) {
            ev.preventDefault();
            ev.stopPropagation();

            const firstInvalid = $('.is-invalid:first');
            if (firstInvalid.length) {
                $('html, body').animate({
                    scrollTop: firstInvalid.offset().top - 100
                }, 500);
            }
            return false;
        }

        if (!$('.submit-spinner').length) {
            $('#apply-btn').append('<span class="submit-spinner ms-2"><i class="fa fa-spinner fa-spin"></i></span>');
        }
        return true;
    },

    // Initialize widget
    start() {
        publicWidget.Widget.prototype.start.apply(this, arguments);
        this._initFormExtensions();

        // Prevent Odoo's default file handling for all file inputs
        $('input[type="file"]').each(function() {
            $(this).attr('data-oe-file-widget', 'false');
        });

        return this;
    },

    // Initialize form extensions
    _initFormExtensions() {
        const presentAddressField = $('textarea[name="present_address"]').closest('.form-group');
        const sameAddressHtml = `
            <div class="form-check mt-2">
                <input type="checkbox" name="is_same_address" id="is_same_address" class="form-check-input"/>
                <label for="is_same_address" class="form-check-label">Same as permanent address</label>
            </div>
        `;
        presentAddressField.append(sameAddressHtml);

        const linkedinField = $('#recruitment4');
        linkedinField.after('<div class="char-counter text-muted small mt-1" id="linkedin-counter"></div>');
        linkedinField.on('input', this._updateCharCounter.bind(this));

        // Fix for employment rows
        const firstEmploymentRow = $('.employment-rows tr:first');
        if (firstEmploymentRow.length) {
            if (firstEmploymentRow.find('.delete-employment-row').length === 0) {
                firstEmploymentRow.append('<td><button type="button" class="btn btn-sm btn-danger delete-employment-row" disabled><i class="fa fa-trash"></i></button></td>');
            }
        }

        const firstSkillRow = $('.skills-rows tr:first');
        if (firstSkillRow.length) {
            firstSkillRow.find('.delete-skill-row').prop('disabled', true);
        }

        this._initTooltips();
        this._onMaritalStatusChange();
        this._setupDateValidations();
    },

    // Initialize tooltips
    _initTooltips() {
        $('[data-toggle="tooltip"]').tooltip();
        $('#recruitment4').attr({
            'data-toggle': 'tooltip',
            'data-placement': 'top',
            'title': _t('Enter a valid LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)')
        });
        $('input[type="file"]').attr({
            'data-toggle': 'tooltip',
            'data-placement': 'top',
            'title': _t('Accepted formats: PDF, DOC, DOCX, JPG, PNG. Maximum size: 5MB')
        });
        $('select[name^="candidate_skill_ids"][name$="[skill_type_id]"]').attr({
            'data-toggle': 'tooltip',
            'data-placement': 'top',
            'title': _t('Select the type of skill (e.g., Technical, Soft Skills)')
        });
    },

    // Setup date validations
    _setupDateValidations() {
        const dobField = $('input[name="dob"]');
        if (dobField.length) {
            const today = new Date();
            const maxDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
            const maxDateStr = maxDate.toISOString().split('T')[0];
            dobField.attr('max', maxDateStr);
        }
        $('input[name^="employment_ids"][name$="[duration_from]"]').on('change', function() {
            const toInput = $(this).closest('td').find('input[name$="[duration_to]"]');
            toInput.attr('min', $(this).val());
        });
    },

    // Handle marital status change
    _onMaritalStatusChange(ev) {
        const maritalStatus = $('select[name="marital_status"]').val();
        const spouseField = $('input[name="spouse_name"]').closest('.form-group');
        if (maritalStatus === 'yes') {
            spouseField.removeClass('d-none');
            spouseField.find('input').attr('required', 'required');
        } else {
            spouseField.addClass('d-none');
            spouseField.find('input').removeAttr('required');
        }
    },

    // Add new employment row
    _onAddEmploymentRow(ev) {
        ev.preventDefault();
        const tbody = $('.employment-rows');
        const currentRows = tbody.find('tr').length;
        if (currentRows >= 5) {
            alert(_t("Maximum of 5 employment records allowed."));
            return;
        }

        const newRow = tbody.find('tr:first').clone(false);
        newRow.attr('data-row', currentRows);

        newRow.find('input, select, textarea').val('');
        const fileCell = newRow.find('td').eq(-2);
        fileCell.empty();
        fileCell.html(`
            <div class="s_website_form_field">
                <input type="file" name="employment_ids[${currentRows}][attachment_ids]" 
                       class="form-control s_website_form_input" multiple="multiple"
                       data-oe-file-widget="false"/>
                <div class="file-previews"></div>
            </div>
        `);

        newRow.find('[name^="employment_ids"]').each(function() {
            const name = $(this).attr('name').replace(/\[\d+\]/, `[${currentRows}]`);
            $(this).attr('name', name);
        });

        const deleteBtn = newRow.find('.delete-employment-row')
            .prop('disabled', false)
            .off('click')
            .on('click', this._onDeleteEmploymentRow.bind(this));

        tbody.append(newRow);
        newRow.find('input[type="file"]').on('change', this._onFileChange.bind(this));

        if (tbody.find('tr').length > 1) {
            $('.delete-employment-row').prop('disabled', false);
        }
    },

    // Delete employment row
    _onDeleteEmploymentRow(ev) {
        ev.preventDefault();
        const tbody = $('.employment-rows');
        const row = $(ev.currentTarget).closest('tr');

        if (tbody.find('tr').length <= 1) {
            row.find('input, select, textarea').val('');
            row.find('.file-previews').empty();
            return;
        }

        row.remove();
        if (tbody.find('tr').length <= 1) {
            $('.delete-employment-row').prop('disabled', true);
        }
        this._reindexEmploymentRows();
    },

    // Reindex employment rows
    _reindexEmploymentRows() {
        $('.employment-rows tr').each(function(index) {
            $(this).attr('data-row', index);
            $(this).find('[name^="employment_ids"]').each(function() {
                const name = $(this).attr('name');
                const newName = name.replace(/\[\d+\]/, `[${index}]`);
                $(this).attr('name', newName);
            });
        });
    },

    // Add new skill row
    _onAddSkillRow(ev) {
        ev.preventDefault();
        const tbody = $('.skills-rows');
        const currentRows = tbody.find('tr').length;
        if (currentRows >= 10) {
            alert('You can add a maximum of 10 skills');
            return;
        }
        
        const newRow = tbody.find('tr:first').clone(true);
        newRow.attr('data-row', currentRows);
        
        // Reset all select fields in the new row
        newRow.find('select').each(function() {
            $(this).val('');
            const name = $(this).attr('name');
            if (name) {
                const newName = name.replace(/\[\d+\]/, `[${currentRows}]`);
                $(this).attr('name', newName);
            }
        });
        
        // Enable delete button
        newRow.find('.delete-skill-row').prop('disabled', false);
        
        tbody.append(newRow);
        
        if (tbody.find('tr').length > 1) {
            tbody.find('.delete-skill-row').prop('disabled', false);
        }
    },

    // Delete skill row
    _onDeleteSkillRow(ev) {
        ev.preventDefault();
        const tbody = $('.skills-rows');
        const row = $(ev.currentTarget).closest('tr');
        if (tbody.find('tr').length <= 1) {
            row.find('select').val('');
            return;
        }
        row.remove();
        if (tbody.find('tr').length <= 1) {
            $('.delete-skill-row').prop('disabled', true);
        }
        this._reindexSkillRows();
    },

    // Reindex skill rows
    _reindexSkillRows() {
        $('.skills-rows tr').each(function(index) {
            $(this).attr('data-row', index);
            $(this).find('[name^="candidate_skill_ids"]').each(function() {
                const name = $(this).attr('name');
                const newName = name.replace(/\[\d+\]/, `[${index}]`);
                $(this).attr('name', newName);
            });
        });
    },

    // Fetch skills and levels using the custom public RPC route
    _onSkillTypeChange(ev) {
        const row = $(ev.currentTarget).closest('tr');
        const skillTypeId = parseInt($(ev.currentTarget).val());
        const skillSelect = row.find('select[name$="[skill_id]"]');
        const levelSelect = row.find('select[name$="[skill_level_id]"]');
        
        // Clear existing options
        skillSelect.empty();
        skillSelect.append('<option value="">Select Skill</option>');
        levelSelect.empty();
        levelSelect.append('<option value="">Select Proficiency</option>');
        
        if (skillTypeId) {
            $.ajax({
                url: '/website_hr_recruitment/get_skills_by_type',
                type: 'POST',
                dataType: 'json',
                contentType: 'application/json',
                data: JSON.stringify({
                    jsonrpc: '2.0',
                    params: {
                        skill_type_id: skillTypeId
                    }
                }),
                success: function(result) {
                    if (result.result && result.result.skills) {
                        const skills = result.result.skills;
                        skills.forEach(skill => {
                            skillSelect.append($('<option>', {
                                value: skill.id,
                                text: skill.name
                            }));
                        });
                    }
                    if (result.result && result.result.levels) {
                        const levels = result.result.levels;
                        levels.forEach(level => {
                            levelSelect.append($('<option>', {
                                value: level.id,
                                text: level.name
                            }));
                        });
                    }
                    if (result.error) {
                        console.error('Error fetching data:', result.error);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Request failed:', error);
                }
            });
        }
    },

    // Calculate experience based on duration
    _calculateExperience(ev) {
        const row = $(ev.currentTarget).closest('tr');
        const fromDate = new Date(row.find('input[name$="[duration_from]"]').val());
        const toDateInput = row.find('input[name$="[duration_to]"]');
        let toDate = toDateInput.val() ? new Date(toDateInput.val()) : new Date();
        if (fromDate && toDate && !isNaN(fromDate) && !isNaN(toDate)) {
            const diffTime = toDate - fromDate;
            const diffYears = diffTime / (1000 * 60 * 60 * 24 * 365.25);
            row.find('input[name$="[years_of_experience]"]').val(diffYears.toFixed(1));
        }
    },

    // Validate education fields
    _validateEducationFields(ev) {
        const row = $(ev.currentTarget).closest('tr');
        const examValue = $(ev.currentTarget).val();
        if (examValue) {
            row.find('textarea[name$="[subject]"]').attr('required', 'required');
            row.find('input[name$="[year_of_passing]"]').attr('required', 'required');
            row.find('select[name$="[study_type]"]').attr('required', 'required');
        } else {
            row.find('textarea, input, select').removeAttr('required');
        }
    },

    // Set document validation rules
    _setDocumentValidation(ev) {
        const row = $(ev.currentTarget).closest('tr');
        const docType = $(ev.currentTarget).val();
        row.find('input[type="text"], input[type="date"]').removeAttr('required');
        if (docType) {
            row.find('input[name$="[name_on_document]"]').attr('required', 'required');
            row.find('input[name$="[document_no]"]').attr('required', 'required');
            row.find('input[name$="[attachment_ids]"]').attr('required', 'required');
            if (['passport', 'aadhar', 'pan'].includes(docType)) {
                row.find('input[name$="[valid_from]"]').attr('required', 'required');
                if (docType === 'passport') {
                    row.find('input[name$="[valid_to]"]').attr('required', 'required');
                }
            }
        }
    },

    // Handle file delete click
    _onFileDeleteClick(ev) {
        ev.preventDefault();
        const $target = $(ev.currentTarget);
        const $preview = $target.closest('.file-preview');
        if ($preview.length) {
            $preview.remove();
        }
    },

    // Handle file input change
    _onFileChange(ev) {
        const fileInput = ev.currentTarget;
        const $container = $(fileInput).closest('.s_website_form_field');
        let $previewsContainer = $container.find('.file-previews');
        if (!$previewsContainer.length) {
            $previewsContainer = $('<div class="file-previews mt-2"></div>');
            $container.append($previewsContainer);
        }
        $previewsContainer.empty();

        if (fileInput.files && fileInput.files.length > 0) {
            Array.from(fileInput.files).forEach(file => {
                const preview = $(`
                    <div class="file-preview mb-1 d-flex align-items-center">
                        <span class="me-2"><i class="fa fa-file"></i> ${file.name}</span>
                        <button type="button" class="btn btn-sm btn-outline-danger delete-file">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                `);
                preview.find('.delete-file').on('click', (e) => {
                    e.preventDefault();
                    preview.remove();
                    if ($previewsContainer.children().length === 0) {
                        $(fileInput).val('');
                    }
                });
                $previewsContainer.append(preview);
            });
        }
    },

    // Check if same address checkbox should be enabled
    _onSameAddressCheck(ev) {
        const permanentAddress = $('textarea[name="permanent_address"]').val();
        $('#is_same_address').prop('disabled', !permanentAddress);
    },

    // Toggle same address
    _onSameAddressToggle(ev) {
        if ($(ev.currentTarget).is(':checked')) {
            const permanentAddress = $('textarea[name="permanent_address"]').val();
            $('textarea[name="present_address"]').val(permanentAddress);
        } else {
            $('textarea[name="present_address"]').val('');
        }
    },

    // Validate salary fields
    _validateSalary(ev) {
        const value = parseFloat($(ev.currentTarget).val());
        if (value < 0) {
            $(ev.currentTarget).val(0);
        }
        const presentSalary = parseFloat($('input[name="present_salary"]').val()) || 0;
        const expectedSalary = parseFloat($('input[name="salary_expected"]').val()) || 0;
        if (presentSalary > 0 && expectedSalary > 0 && expectedSalary < presentSalary) {
            if (!$('#salary-warning').length) {
                $('input[name="salary_expected"]').after(
                    '<div id="salary-warning" class="text-warning small mt-1">' +
                    _t("Expected salary is less than your present salary.") +
                    '</div>'
                );
            }
        } else {
            $('#salary-warning').remove();
        }
    },

    // Validate file size and type
    _validateFileSize(ev) {
        const files = ev.currentTarget.files;
        if (!files) return;
        const maxSize = 5 * 1024 * 1024; // 5MB
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png'];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.size > maxSize) {
                alert(_t("File size exceeds maximum limit of 5MB: ") + file.name);
                ev.currentTarget.value = '';
                return;
            }
            const fileExt = file.name.split('.').pop().toLowerCase();
            const isValidExt = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'].includes(fileExt);
            if (!isValidExt && !allowedTypes.includes(file.type)) {
                alert(_t("Invalid file type. Please upload PDF, DOC, DOCX, JPG or PNG files only."));
                ev.currentTarget.value = '';
                return;
            }
        }
    },

    // Update character counter for LinkedIn field
    _updateCharCounter(ev) {
        const target = $(ev.currentTarget);
        const counter = $(`#${target.attr('id')}-counter`);
        const maxLength = parseInt(target.attr('maxlength') || 150);
        const currentLength = target.val().length;
        counter.text(`${currentLength}/${maxLength}`);
        if (currentLength > maxLength * 0.8) {
            counter.addClass('text-warning');
        } else {
            counter.removeClass('text-warning');
        }
    },

    // Validate entire form
    _validateForm() {
        let isValid = true;
        $('#hr_recruitment_form [required]').each(function() {
            if (!$(this).val()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        const linkedinProfile = $('#recruitment4').val();
        const resume = $('#recruitment6')[0]?.files.length;
        if (!linkedinProfile && !resume) {
            $('#recruitment4').addClass('is-invalid');
            $('#recruitment6').addClass('is-invalid');
            if (!$('#profile-required-warning').length) {
                $('#recruitment6').after(
                    '<div id="profile-required-warning" class="text-danger mt-2">' +
                    _t("Please provide either a LinkedIn profile or upload a resume.") +
                    '</div>'
                );
            }
            isValid = false;
        } else {
            $('#recruitment4').removeClass('is-invalid');
            $('#recruitment6').removeClass('is-invalid');
            $('#profile-required-warning').remove();
        }
        
        $('.employment-rows tr').each(function() {
            const fromDate = $(this).find('input[name$="[duration_from]"]').val();
            const toDate = $(this).find('input[name$="[duration_to]"]').val();
            if (fromDate && toDate && new Date(fromDate) > new Date(toDate)) {
                $(this).find('input[name$="[duration_from]"], input[name$="[duration_to]"]').addClass('is-invalid');
                isValid = false;
            }
        });
        
        let skillsFilled = 0;
        $('.skills-rows tr').each(function() {
            const skillType = $(this).find('select[name$="[skill_type_id]"]').val();
            const skill = $(this).find('select[name$="[skill_id]"]').val();
            const level = $(this).find('select[name$="[skill_level_id]"]').val();
            if (skillType && skill && level) {
                skillsFilled++;
            }
        });
        if (skillsFilled === 0) {
            $('.skills-rows tr:first select').addClass('is-invalid');
            if (!$('#skills-required-warning').length) {
                $('.skills-rows').after(
                    '<div id="skills-required-warning" class="text-danger mt-2">' +
                    _t("Please provide at least one skill.") +
                    '</div>'
                );
            }
            isValid = false;
        } else {
            $('.skills-rows select').removeClass('is-invalid');
            $('#skills-required-warning').remove();
        }
        
        return isValid;
    },

    // Check form completeness (optional)
    _checkFormCompleteness() {
        let educationFilled = 0;
        $('select[name^="education_ids"][name$="[exam_passed]"]').each(function() {
            if ($(this).val()) {
                educationFilled++;
            }
        });
        let documentsFilled = 0;
        $('select[name^="document_ids"][name$="[document_type]"]').each(function() {
            if ($(this).val()) {
                documentsFilled++;
            }
        });
        if (educationFilled === 0) {
            alert(_t("Please provide at least one education record."));
            return false;
        }
        if (documentsFilled === 0) {
            alert(_t("Please provide at least one document record."));
            return false;
        }
        return true;
    }
});

// Document ready enhancements
$(document).ready(function() {
    $('#hr_recruitment_form').addClass('recruitment-extended-form');
    const sections = ['Personal Information', 'Contact Information', 'Health Information',
                     'Address Information', 'Salary and Experience', 'Referral', 'Skills',
                     'Education / Qualification', 'Employment History', 'Document Details'];
    let navHtml = '<div class="form-nav-container mb-4"><ul class="nav nav-pills nav-justified form-nav">';
    sections.forEach((section, index) => {
        navHtml += `<li class="nav-item">
            <a class="nav-link ${index === 0 ? 'active' : ''}" href="#section-${index}">${section}</a>
        </li>`;
    });
    navHtml += '</ul></div>';
    $('#hr_recruitment_form').prepend(navHtml);
    $('#hr_recruitment_form h3').each(function(index) {
        $(this).attr('id', `section-${index}`);
        $(this).addClass('section-heading');
    });
    $('.form-nav a').on('click', function(e) {
        e.preventDefault();
        const target = $(this.getAttribute('href'));
        if (target.length) {
            $('.form-nav a').removeClass('active');
            $(this).addClass('active');
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 500);
        }
    });
    $(window).on('scroll', function() {
        const scrollPos = $(document).scrollTop();
        $('#hr_recruitment_form h3').each(function(index) {
            const target = $(this);
            if (target.offset().top - 100 <= scrollPos) {
                $('.form-nav a').removeClass('active');
                $(`.form-nav a[href="#${target.attr('id')}"]`).addClass('active');
            }
        });
    });
});

// Add custom styles
const style = document.createElement('style');
style.textContent = `
.recruitment-extended-form h3 {
    border-bottom: 2px solid #dee2e6;
    padding-bottom: 10px;
    margin-top: 30px;
    margin-bottom: 20px;
    color: #495057;
}
.form-nav-container {
    position: sticky;
    top: 0;
    z-index: 100;
    background: white;
    padding: 10px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.form-nav .nav-link {
    padding: 5px;
    font-size: 12px;
}
.section-heading {
    scroll-margin-top: 80px;
}
.o_linkedin_icon {
    position: absolute;
    margin-top: 10px;
    margin-left: 10px;
    color: #0077B5;
}
.is-invalid {
    border-color: #dc3545;
}
.employment-rows tr:hover, .skills-rows tr:hover {
    background-color: #f8f9fa;
}
.file-previews {
    margin-top: 5px;
}
.file-preview {
    background-color: #f8f9fa;
    padding: 5px 10px;
    border-radius: 4px;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
}
.file-preview .delete-file {
    margin-left: auto;
    padding: 0.25rem 0.5rem;
}
`;
document.head.appendChild(style);

export default publicWidget.registry.hrRecruitmentExtended;