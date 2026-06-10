from odoo import models, fields, api

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    asd_type = fields.Char(string='Type')
    amount = fields.Monetary(string='Amount', compute='_compute_amount', store=True)
    currency_id = fields.Many2one(related='contract_id.company_id.currency_id')

    @api.depends('number_of_days', 'contract_id.wage')
    def _compute_amount(self):
        for record in self:
            if record.contract_id and record.contract_id.wage:
                # Assuming 30 days standard month for simple amount calculation
                daily_wage = record.contract_id.wage / 30.0
                record.amount = record.number_of_days * daily_wage
            else:
                record.amount = 0.0

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    asd_monthly_sheet_id = fields.Many2one('attendance.monthly.sheet', string='Attendance Sheet', compute='_compute_asd_monthly_sheet', store=True)
    asd_total_days = fields.Float(string='Total Days', compute='_compute_worked_days_totals', store=True)
    asd_total_hours = fields.Float(string='Total Hours', compute='_compute_worked_days_totals', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    asd_total_amount = fields.Monetary(string='Total Amount', compute='_compute_worked_days_totals', store=True, currency_field='currency_id')

    @api.depends('date_from', 'employee_id')
    def _compute_asd_monthly_sheet(self):
        for record in self:
            if record.employee_id and record.date_from:
                month_str = str(record.date_from.month)
                year_str = str(record.date_from.year)
                sheet = self.env['attendance.monthly.sheet'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('month', '=', month_str),
                    ('year', '=', year_str)
                ], limit=1)
                record.asd_monthly_sheet_id = sheet.id
            else:
                record.asd_monthly_sheet_id = False

    @api.depends('worked_days_line_ids.number_of_days', 'worked_days_line_ids.number_of_hours', 'worked_days_line_ids.amount')
    def _compute_worked_days_totals(self):
        for record in self:
            record.asd_total_days = sum(line.number_of_days for line in record.worked_days_line_ids)
            record.asd_total_hours = sum(line.number_of_hours for line in record.worked_days_line_ids)
            record.asd_total_amount = sum(line.amount for line in record.worked_days_line_ids)

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        # Override standard worked day lines or return our own list
        res = super(HrPayslip, self)._get_worked_day_lines(domain=domain, check_out_of_contract=check_out_of_contract)
        return res
        
    def compute_sheet(self):
        for payslip in self:
            # Delete old lines
            payslip.worked_days_line_ids.unlink()
            
            lines = []
            sheet = payslip.asd_monthly_sheet_id
            if sheet:
                # Basic Mapping
                company_hours = payslip.company_id.asd_daily_working_hours if hasattr(payslip.company_id, 'asd_daily_working_hours') and payslip.company_id.asd_daily_working_hours else 8.0
                
                if sheet.present_days > 0:
                    lines.append((0, 0, {
                        'name': 'Attendance Worked', 'sequence': 10, 'code': 'P', 'asd_type': 'Present Days',
                        'number_of_days': sheet.present_days, 'number_of_hours': sheet.present_days * company_hours, 'contract_id': payslip.contract_id.id
                    }))
                if sheet.weekly_off_days > 0:
                    lines.append((0, 0, {
                        'name': 'Weekly Off Paid', 'sequence': 11, 'code': 'WO', 'asd_type': 'Weekly Off',
                        'number_of_days': sheet.weekly_off_days, 'number_of_hours': sheet.weekly_off_days * company_hours, 'contract_id': payslip.contract_id.id
                    }))
                if sheet.public_holiday_days > 0:
                    lines.append((0, 0, {
                        'name': 'Public Holiday Paid', 'sequence': 12, 'code': 'PH', 'asd_type': 'Public Holiday',
                        'number_of_days': sheet.public_holiday_days, 'number_of_hours': sheet.public_holiday_days * company_hours, 'contract_id': payslip.contract_id.id
                    }))
                if sheet.leave_days > 0:
                    lines.append((0, 0, {
                        'name': 'Paid Leave', 'sequence': 13, 'code': 'LEAVE', 'asd_type': 'Paid Leave',
                        'number_of_days': sheet.leave_days, 'number_of_hours': sheet.leave_days * company_hours, 'contract_id': payslip.contract_id.id
                    }))
                if sheet.lop_days > 0:
                    lines.append((0, 0, {
                        'name': 'Unpaid Leave (LOP)', 'sequence': 14, 'code': 'LOP', 'asd_type': 'LOP',
                        'number_of_days': sheet.lop_days, 'number_of_hours': sheet.lop_days * company_hours, 'contract_id': payslip.contract_id.id
                    }))
                if sheet.overtime_hours > 0:
                    lines.append((0, 0, {
                        'name': 'Extra Hours', 'sequence': 15, 'code': 'OT', 'asd_type': 'Overtime',
                        'number_of_days': 0, 'number_of_hours': sheet.overtime_hours, 'contract_id': payslip.contract_id.id
                    }))
            
                payslip.worked_days_line_ids = lines
            
        return super(HrPayslip, self).compute_sheet()
