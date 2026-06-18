# -*- coding: utf-8 -*-
import base64
import json
import time
from datetime import date

import pytz
from odoo import http
from odoo.http import request, route, Controller
from odoo.exceptions import UserError, ValidationError
from odoo.addons.portal.controllers.web import Home as PortalHome
from odoo.addons.web.controllers.utils import is_user_internal


class EssHome(PortalHome):
    """Override portal login redirect: portal users with a matching hr.employee
    (matched by work_email = user login) are sent to /ess instead of /my."""

    def _login_redirect(self, uid, redirect=None):
        if not redirect and not is_user_internal(uid):
            login = request.env['res.users'].sudo().browse(uid).login
            has_employee = request.env['hr.employee'].sudo().search_count(
                [('work_email', '=', login)], limit=1
            )
            if has_employee:
                redirect = '/ess'
        return super()._login_redirect(uid, redirect=redirect)

    @http.route()
    def index(self, *args, **kw):
        if request.session.uid and not is_user_internal(request.session.uid):
            login = request.env.user.login
            has_employee = request.env['hr.employee'].sudo().search_count(
                [('work_email', '=', login)], limit=1
            )
            if has_employee:
                return request.redirect_query('/ess', query=request.params)
        return super().index(*args, **kw)


class OwlSelfServiceController(Controller):

    @route("/ess", auth="user", website=True)
    def standalone_app(self):
        session_info = request.env['ir.http'].get_frontend_session_info()
        user = request.env.user
        partner = user.partner_id
        has_avatar = bool(partner.image_128) if partner else False
        session_info.update({
            'uid': request.session.uid,
            'partner_id': partner.id if partner else None,
            'has_avatar': has_avatar,
        })
        return request.render(
            'owl_self_service.standalone_app',
            {
                'session_info': session_info,
                'json': json,
            }
        )

    def _get_employee_by_email(self):
        """Find employee whose work_email matches the current user's login (email)."""
        login = request.env.user.login
        return request.env['hr.employee'].sudo().search(
            [('work_email', '=', login)], limit=1
        )

    def _get_employee_or_error(self, empty=None):
        """Return (employee, None) or (None, error_dict). empty overrides the error payload."""
        employee = self._get_employee_by_email()
        if not employee:
            return None, empty if empty is not None else {'error': 'no_employee'}
        return employee, None

    def _get_valid_leave_types(self, employee):
        """Return hr.leave.type records valid for this employee:
        either no allocation required, or has a validated allocation this year."""
        today = date.today()
        year_start = today.strftime('%Y-01-01')
        year_end = today.strftime('%Y-12-31')

        allocated_ids = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', year_end),
            '|',
            ('date_to', '>=', year_start),
            ('date_to', '=', False),
        ]).mapped('holiday_status_id').ids

        all_types = request.env['hr.leave.type'].with_context(
            employee_id=employee.id
        ).sudo().search([('active', '=', True)])

        return all_types.filtered(
            lambda lt: lt.requires_allocation != 'yes' or lt.id in allocated_ids
        )

    @route('/ess/attendance/status', type='json', auth='user')
    def attendance_status(self):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        open_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)

        return {
            'employee_id': employee.id,
            'employee_name': employee.name,
            'attendance_state': 'checked_in' if open_attendance else 'checked_out',
            'last_check_in': open_attendance.check_in.strftime('%Y-%m-%dT%H:%M:%SZ') if open_attendance and open_attendance.check_in else False,
        }

    @route('/ess/attendance/toggle', type='json', auth='user')
    def attendance_toggle(self):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        try:
            employee.sudo()._attendance_action_change()
        except UserError as e:
            return {'error': str(e)}

        open_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)

        return {
            'attendance_state': 'checked_in' if open_attendance else 'checked_out',
            'last_check_in': open_attendance.check_in.strftime('%Y-%m-%dT%H:%M:%SZ') if open_attendance and open_attendance.check_in else False,
        }

    @route('/ess/attendance/history', type='json', auth='user')
    def attendance_history(self, page=1, limit=10):
        employee, err = self._get_employee_or_error({'error': 'no_employee', 'records': [], 'total': 0})
        if err:
            return err

        offset = (page - 1) * limit
        domain = [('employee_id', '=', employee.id)]

        records = request.env['hr.attendance'].sudo().search_read(
            domain,
            ['id', 'check_in', 'check_out'],
            limit=limit,
            offset=offset,
            order='check_in desc',
        )
        total = request.env['hr.attendance'].sudo().search_count(domain)

        def fmt(dt):
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ') if dt else False

        return {
            'records': [
                {
                    'id': r['id'],
                    'employee_name': employee.name,
                    'check_in': fmt(r['check_in']),
                    'check_out': fmt(r['check_out']),
                }
                for r in records
            ],
            'total': total,
        }

    # ── Payslip ────────────────────────────────────────────────────────

    @route('/ess/payslips/list', type='json', auth='user')
    def payslip_list(self, page=1, limit=10):
        employee, err = self._get_employee_or_error({'error': 'no_employee', 'records': [], 'total': 0})
        if err:
            return err

        try:
            domain = [('employee_id', '=', employee.id)]
            offset = (page - 1) * limit
            payslips = request.env['hr.payslip'].sudo().search(
                domain, order='date_from desc', limit=limit, offset=offset
            )
            total = request.env['hr.payslip'].sudo().search_count(domain)

            records = []
            state_dict = dict(request.env['hr.payslip']._fields['state'].selection)
            for slip in payslips:
                records.append({
                    'id': slip.id,
                    'name': slip.name or slip.number or 'Payslip',
                    'date_from': slip.date_from.strftime('%b %d, %Y') if slip.date_from else '',
                    'date_to': slip.date_to.strftime('%b %d, %Y') if slip.date_to else '',
                    'amount': slip.net_wage if hasattr(slip, 'net_wage') else sum(slip.line_ids.filtered(lambda l: l.code == 'NET').mapped('total')),
                    'currency': slip.company_id.currency_id.symbol or '',
                    'state': slip.state,
                    'state_label': state_dict.get(slip.state, slip.state),
                })
            return {'records': records, 'total': total}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/ess/payslips/download/<int:slip_id>', type='http', auth='user')
    def payslip_pdf(self, slip_id, **kw):
        slip = request.env['hr.payslip'].sudo().browse(slip_id)
        employee = self._get_employee_by_email()
        if not slip or not employee or slip.employee_id.id != employee.id:
            return request.not_found()
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf('hr_payroll.action_report_payslip', [slip.id])
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    # ── Contract ───────────────────────────────────────────────────────

    @route('/ess/contract/active', type='json', auth='user')
    def contract_active(self):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        contract = request.env['hr.contract'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'open'),
        ], limit=1, order='date_start desc')

        if not contract:
            return {'contract': False}

        return {
            'contract': {
                'id': contract.id,
                'name': contract.name,
                'date_start': contract.date_start.strftime('%Y-%m-%d') if contract.date_start else False,
                'date_end': contract.date_end.strftime('%Y-%m-%d') if contract.date_end else False,
                'wage': contract.wage,
                'currency_symbol': contract.currency_id.symbol or '',
                'job_title': contract.job_id.name if contract.job_id else (employee.job_title or ''),
                'department': contract.department_id.name if contract.department_id else '',
                'company': contract.company_id.name if contract.company_id else '',
            }
        }

    # ── Expense ────────────────────────────────────────────────────────

    _EXPENSE_STATE_LABEL = {
        'draft':   'To Submit',
        'submit':  'Submitted',
        'approve': 'Approved',
        'post':    'Done',
        'done':    'Done',
        'cancel':  'Refused',
    }

    _EXPENSE_STATE_COLOR = {
        'draft':   'gray',
        'submit':  'blue',
        'approve': 'green',
        'post':    'green',
        'done':    'green',
        'cancel':  'red',
    }

    def _get_draft_sheet(self, sheet_id, employee):
        return request.env['hr.expense.sheet'].sudo().search([
            ('id', '=', sheet_id),
            ('employee_id', '=', employee.id),
            ('state', '=', 'draft'),
        ], limit=1)

    def _fmt_expense(self, sheet):
        first_line = sheet.expense_line_ids[:1]
        effective_date = sheet.accounting_date or (first_line.date if first_line else False)
        return {
            'id': sheet.id,
            'employee_name': sheet.employee_id.name if sheet.employee_id else '',
            'name': sheet.name,
            'date': effective_date.strftime('%Y-%m-%d') if effective_date else False,
            'total_amount': sheet.total_amount,
            'currency_symbol': sheet.currency_id.symbol or '',
            'state': sheet.state,
            'state_label': self._EXPENSE_STATE_LABEL.get(sheet.state, sheet.state),
            'state_color': self._EXPENSE_STATE_COLOR.get(sheet.state, 'gray'),
            'product_id': first_line.product_id.id if first_line else False,
            'description': first_line.description if first_line else '',
        }

    @route('/ess/expense/list', type='json', auth='user')
    def expense_list(self, page=1, limit=10, filterby='all', sortby='date', date_from=False, date_to=False):
        employee, err = self._get_employee_or_error({'error': 'no_employee', 'records': [], 'total': 0})
        if err:
            return err

        state_map = {
            'draft':   [('state', '=', 'draft')],
            'submit':  [('state', '=', 'submit')],
            'approve': [('state', '=', 'approve')],
            'done':    [('state', 'in', ('post', 'done'))],
            'cancel':  [('state', '=', 'cancel')],
        }
        order_map = {
            'date':   'id desc',
            'name':   'name asc',
            'state':  'state asc',
            'amount': 'total_amount desc',
        }

        domain = [('employee_id', '=', employee.id)]
        if filterby in state_map:
            domain += state_map[filterby]
        if date_from:
            domain.append(('expense_line_ids.date', '>=', date_from))
        if date_to:
            domain.append(('expense_line_ids.date', '<=', date_to))

        order = order_map.get(sortby, order_map['date'])
        offset = (page - 1) * limit

        sheets = request.env['hr.expense.sheet'].sudo().search(
            domain, order=order, limit=limit, offset=offset
        )
        total = request.env['hr.expense.sheet'].sudo().search_count(domain)

        return {
            'records': [self._fmt_expense(s) for s in sheets],
            'total': total,
        }

    @route('/ess/expense/products', type='json', auth='user')
    def expense_products(self):
        products = request.env['product.product'].sudo().search([
            ('can_be_expensed', '=', True),
            ('active', '=', True),
        ], order='name asc', limit=100)
        return [{'id': p.id, 'name': p.name} for p in products]

    @route('/ess/expense/create', type='json', auth='user')
    def expense_create(self, name, product_id, total_amount, expense_date=False, description='', sheet_name=''):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        try:
            vals = {
                'name': (name or '').strip(),
                'employee_id': employee.id,
                'product_id': int(product_id),
                'total_amount_currency': float(total_amount),
                'date': expense_date or date.today().strftime('%Y-%m-%d'),
                'description': (description or '').strip(),
            }
            expense = request.env['hr.expense'].sudo().create(vals)
            sheet = request.env['hr.expense.sheet'].sudo().create({
                'name': (sheet_name or name or '').strip(),
                'employee_id': employee.id,
                'expense_line_ids': [(4, expense.id)],
            })
        except (ValueError, ValidationError) as e:
            return {'error': str(e)}

        return {'success': True, 'sheet_id': sheet.id}

    @route('/ess/expense/update', type='json', auth='user')
    def expense_update(self, sheet_id, name, product_id, total_amount, expense_date=False, description=''):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        sheet = self._get_draft_sheet(sheet_id, employee)
        if not sheet:
            return {'error': 'Expense not found or cannot be edited.'}

        try:
            sheet.write({'name': (name or '').strip()})
            if sheet.expense_line_ids:
                sheet.expense_line_ids[0].write({
                    'name': (name or '').strip(),
                    'product_id': int(product_id),
                    'total_amount_currency': float(total_amount),
                    'date': expense_date or date.today().strftime('%Y-%m-%d'),
                    'description': (description or '').strip(),
                })
        except (ValueError, ValidationError) as e:
            return {'error': str(e)}

        return {'success': True}

    @route('/ess/expense/delete', type='json', auth='user')
    def expense_delete(self, sheet_id):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        sheet = self._get_draft_sheet(sheet_id, employee)
        if not sheet:
            return {'error': 'Expense not found or cannot be deleted.'}

        sheet.expense_line_ids.unlink()
        sheet.unlink()
        return {'success': True}

    # ── Time Off ───────────────────────────────────────────────────────

    _LEAVE_STATE_LABEL = {
        'draft':    'To Submit',
        'confirm':  'To Approve',
        'validate1': 'Second Approval',
        'validate': 'Approved',
        'refuse':   'Refused',
    }

    _LEAVE_STATE_COLOR = {
        'draft':    'gray',
        'confirm':  'blue',
        'validate1': 'orange',
        'validate': 'green',
        'refuse':   'red',
    }

    _LEAVE_COLORS = [
        '#714B67', '#2563eb', '#059669', '#d97706', '#dc2626',
        '#7c3aed', '#0891b2', '#65a30d', '#c026d3', '#ea580c',
    ]

    def _leave_color_hex(self, leave_type):
        color_index = leave_type.color or 0
        return self._LEAVE_COLORS[int(color_index) % len(self._LEAVE_COLORS)]

    @route('/ess/timeoff/balance', type='json', auth='user')
    def timeoff_balance(self):
        employee, err = self._get_employee_or_error({'error': 'no_employee', 'balances': []})
        if err:
            return err

        leave_types = self._get_valid_leave_types(employee)

        balances = []
        for lt in leave_types:
            needs_allocation = lt.requires_allocation == 'yes'
            balances.append({
                'id': lt.id,
                'name': lt.name,
                'color_hex': self._LEAVE_COLORS[int(lt.color or 0) % len(self._LEAVE_COLORS)],
                'requires_allocation': needs_allocation,
                'max_leaves': lt.max_leaves,
                'leaves_taken': lt.leaves_taken,
                'virtual_remaining': lt.virtual_remaining_leaves,
            })

        return {'balances': balances}

    @route('/ess/timeoff/history', type='json', auth='user')
    def timeoff_history(self, page=1, limit=10):
        employee, err = self._get_employee_or_error({'error': 'no_employee', 'records': [], 'total': 0})
        if err:
            return err

        domain = [('employee_id', '=', employee.id)]
        offset = (page - 1) * limit

        leaves = request.env['hr.leave'].sudo().search(
            domain, order='date_from desc', limit=limit, offset=offset
        )
        total = request.env['hr.leave'].sudo().search_count(domain)

        leave_ids = leaves.ids
        attachments = request.env['ir.attachment'].sudo().search_read(
            [('res_model', '=', 'hr.leave'), ('res_id', 'in', leave_ids)],
            ['res_id', 'name'],
        )
        attachment_map = {a['res_id']: a for a in attachments}

        records = []
        for leave in leaves:
            lt = leave.holiday_status_id
            attachment = attachment_map.get(leave.id)
            records.append({
                'id': leave.id,
                'employee_name': leave.employee_id.name if leave.employee_id else '',
                'type_name': lt.name if lt else '',
                'color_hex': self._leave_color_hex(lt) if lt else '#714B67',
                'date_from': leave.date_from.strftime('%Y-%m-%d') if leave.date_from else False,
                'date_to': leave.date_to.strftime('%Y-%m-%d') if leave.date_to else False,
                'number_of_days': leave.number_of_days,
                'description': leave.private_name or '',
                'state': leave.state,
                'state_label': self._LEAVE_STATE_LABEL.get(leave.state, leave.state),
                'state_color': self._LEAVE_STATE_COLOR.get(leave.state, 'gray'),
                'holiday_status_id': leave.holiday_status_id.id if leave.holiday_status_id else False,
                'can_cancel': leave.state in ('draft', 'confirm'),
                'can_edit': leave.state in ('draft', 'confirm'),
                'has_attachment': bool(attachment),
                'attachment_name': attachment['name'] if attachment else '',
            })

        return {'records': records, 'total': total}

    @route('/ess/timeoff/leave_types', type='json', auth='user')
    def timeoff_leave_types(self):
        employee, err = self._get_employee_or_error({'types': []})
        if err:
            return err

        leave_types = self._get_valid_leave_types(employee)

        result = []
        for lt in leave_types:
            result.append({
                'id': lt.id,
                'name': lt.name,
                'request_unit': lt.request_unit,
                'support_document': lt.support_document,
            })

        return {'types': result}

    @route('/ess/timeoff/request', type='json', auth='user')
    def timeoff_request(self, holiday_status_id, date_from, date_to,
                        description='', attachment_b64=None, attachment_name='',
                        request_unit=None, half_day_period='am',
                        hour_from=None, hour_to=None):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        try:
            with request.env.cr.savepoint():
                lt = request.env['hr.leave.type'].sudo().browse(int(holiday_status_id))
                effective_unit = request_unit or lt.request_unit or 'day'

                vals = {
                    'employee_id': employee.id,
                    'holiday_status_id': int(holiday_status_id),
                    'request_date_from': date_from,
                    'request_date_to': date_from if effective_unit in ('half_day', 'hour') else date_to,
                    'private_name': (description or '').strip(),
                }

                if effective_unit == 'half_day':
                    vals['request_unit_half'] = True
                    vals['request_date_from_period'] = half_day_period or 'am'

                elif effective_unit == 'hour':
                    vals['request_unit_hours'] = True
                    vals['request_hour_from'] = str(hour_from) if hour_from is not None else '8'
                    vals['request_hour_to'] = str(hour_to) if hour_to is not None else '17'

                leave = request.env['hr.leave'].sudo().create(vals)

                if attachment_b64 and attachment_name:
                    request.env['ir.attachment'].sudo().create({
                        'name': attachment_name,
                        'datas': attachment_b64,
                        'res_model': 'hr.leave',
                        'res_id': leave.id,
                        'mimetype': 'application/octet-stream',
                    })

                if leave.state == 'draft':
                    leave.write({'state': 'confirm'})
        except (ValueError, ValidationError, UserError) as e:
            return {'error': str(e)}

        return {'success': True, 'leave_id': leave.id}

    @route('/ess/timeoff/calendar_events', type='json', auth='user')
    def timeoff_calendar_events(self):
        employee, err = self._get_employee_or_error({'error': 'no_employee', 'events': []})
        if err:
            return err

        leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', '!=', False),
            ('state', 'in', ('confirm', 'validate1', 'validate')),
        ])

        # date_from/date_to are stored in UTC; convert to user timezone once
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')

        def to_local(dt):
            if not dt:
                return None
            return pytz.utc.localize(dt).astimezone(user_tz)

        events = []
        for leave in leaves:
            lt = leave.holiday_status_id
            df_local = to_local(leave.date_from)
            dt_local = to_local(leave.date_to)

            events.append({
                'id': leave.id,
                'date_from': df_local.strftime('%Y-%m-%d') if df_local else False,
                'date_to': dt_local.strftime('%Y-%m-%d') if dt_local else False,
                'time_from': df_local.strftime('%H:%M') if df_local else False,
                'time_to': dt_local.strftime('%H:%M') if dt_local else False,
                'type_name': lt.name if lt else '',
                'employee_name': leave.employee_id.name if leave.employee_id else '',
                'color_hex': self._leave_color_hex(lt) if lt else '#714B67',
                'number_of_days': leave.number_of_days,
            })

        return {'events': events}

    @route('/ess/timeoff/cancel', type='json', auth='user')
    def timeoff_cancel(self, leave_id):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        leave = request.env['hr.leave'].sudo().search([
            ('id', '=', int(leave_id)),
            ('employee_id', '=', employee.id),
            ('state', 'in', ('draft', 'confirm')),
        ], limit=1)

        if not leave:
            return {'error': 'Request not found or cannot be cancelled.'}

        try:
            if hasattr(leave, 'action_cancel'):
                leave.action_cancel()
            else:
                leave.write({'state': 'draft'})
            leave.unlink()
        except (UserError, ValidationError) as e:
            return {'error': str(e)}

        return {'success': True}

    @route('/ess/timeoff/update', type='json', auth='user')
    def timeoff_update(self, leave_id, holiday_status_id, date_from, date_to,
                       description='', attachment_b64=None, attachment_name='',
                       request_unit=None, half_day_period='am',
                       hour_from=None, hour_to=None):
        employee, err = self._get_employee_or_error()
        if err:
            return err

        leave = request.env['hr.leave'].sudo().search([
            ('id', '=', int(leave_id)),
            ('employee_id', '=', employee.id),
            ('state', 'in', ('draft', 'confirm')),
        ], limit=1)

        if not leave:
            return {'error': 'Request not found or cannot be edited.'}

        try:
            with request.env.cr.savepoint():

                lt = request.env['hr.leave.type'].sudo().browse(int(holiday_status_id))
                effective_unit = request_unit or lt.request_unit or 'day'

                vals = {
                    'holiday_status_id': int(holiday_status_id),
                    'request_date_from': date_from,
                    'request_date_to': date_from if effective_unit in ('half_day', 'hour') else date_to,
                    'private_name': (description or '').strip(),
                    'request_unit_half': False,
                    'request_unit_hours': False,
                }

                if effective_unit == 'half_day':
                    vals['request_unit_half'] = True
                    vals['request_date_from_period'] = half_day_period or 'am'
                elif effective_unit == 'hour':
                    vals['request_unit_hours'] = True
                    vals['request_hour_from'] = str(hour_from) if hour_from is not None else '8'
                    vals['request_hour_to'] = str(hour_to) if hour_to is not None else '17'

                leave.write(vals)

                if attachment_b64 and attachment_name:
                    request.env['ir.attachment'].sudo().create({
                        'name': attachment_name,
                        'datas': attachment_b64,
                        'res_model': 'hr.leave',
                        'res_id': leave.id,
                        'mimetype': 'application/octet-stream',
                    })

                if leave.state == 'draft':
                    leave.write({'state': 'confirm'})
        except (UserError, ValidationError) as e:
            return {'error': str(e)}

        return {'success': True}

    @route('/ess/account/avatar_info', type='json', auth='user')
    def account_avatar_info(self):
        user = request.env.user
        partner = user.partner_id
        employee = self._get_employee_by_email()
        # Employee image takes priority (computed from user avatar or own image)
        if employee and bool(employee.image_128):
            return {
                'source': 'employee',
                'employee_id': employee.id,
                'partner_id': partner.id if partner else None,
                'has_avatar': True,
            }
        has_avatar = bool(partner.image_128) if partner else False
        return {
            'source': 'partner',
            'partner_id': partner.id if partner else None,
            'has_avatar': has_avatar,
        }

    @route('/ess/account/change_password', type='json', auth='user')
    def account_change_password(self, old_password, new_password):
        user = request.env.user
        try:
            user._check_credentials(old_password, {'interactive': False})
        except Exception:
            # _check_credentials raises AccessDenied (not UserError) on wrong password
            return {'error': 'Current password is incorrect.'}
        if len(new_password) < 6:
            return {'error': 'New password must be at least 6 characters.'}
        try:
            user.sudo().write({'password': new_password})
        except (UserError, ValidationError) as e:
            return {'error': str(e)}
        return {'success': True}

    @route('/ess/account/profile', type='json', auth='user')
    def account_profile_get(self):
        partner = request.env.user.partner_id
        emp = self._get_employee_by_email()
        # Employee fields take priority; fallback to partner where employee has no data
        name = (emp.name if emp else None) or partner.name or ''
        street = (emp.sudo().private_street if emp else None) or partner.street or ''
        city = (emp.sudo().private_city if emp else None) or partner.city or ''
        zip_code = (emp.sudo().private_zip if emp else None) or partner.zip or ''
        country_id = (emp.sudo().private_country_id.id if emp and emp.sudo().private_country_id else None) \
                     or (partner.country_id.id if partner.country_id else False)
        return {
            'name': name,
            'email': partner.email or '',
            'company_name': partner.company_name or '',
            'vat': partner.vat or '',
            'street': street,
            'city': city,
            'zip': zip_code,
            'country_id': country_id,
            'work_phone': emp.work_phone or '' if emp else '',
            'mobile_phone': emp.mobile_phone or '' if emp else '',
            'work_email': emp.work_email or '' if emp else '',
            'job_title': emp.job_title or '' if emp else '',
            'department': emp.department_id.name if emp and emp.department_id else '',
            'emergency_contact': emp.emergency_contact or '' if emp else '',
            'emergency_phone': emp.emergency_phone or '' if emp else '',
            'certificate': emp.certificate or '' if emp else '',
            'study_field': emp.study_field or '' if emp else '',
            'study_school': emp.study_school or '' if emp else '',
            'marital': emp.marital or '' if emp else '',
            'children': emp.children or 0 if emp else 0,
            'spouse_complete_name': emp.spouse_complete_name or '' if emp else '',
            'spouse_birthdate': emp.spouse_birthdate.strftime('%Y-%m-%d') if emp and emp.spouse_birthdate else '',
            'has_employee': bool(emp),
        }

    @route('/ess/account/profile/update', type='json', auth='user')
    def account_profile_update(self, **kw):
        partner = request.env.user.partner_id
        emp = self._get_employee_by_email()
        name = kw.get('name') or partner.name
        country_id_int = int(kw.get('country_id')) if kw.get('country_id') else False
        partner_vals = {
            'name': name,
            'company_name': kw.get('company_name') or False,
            'vat': kw.get('vat') or False,
            'street': kw.get('street') or False,
            'city': kw.get('city') or False,
            'zip': kw.get('zip') or False,
            'country_id': country_id_int,
        }
        try:
            partner.sudo().write(partner_vals)
            if emp:
                emp_vals = {
                    'name': name,
                    'work_phone': kw.get('work_phone') or False,
                    'mobile_phone': kw.get('mobile_phone') or False,
                    'private_street': kw.get('street') or False,
                    'private_city': kw.get('city') or False,
                    'private_zip': kw.get('zip') or False,
                    'private_country_id': country_id_int,
                    'emergency_contact': kw.get('emergency_contact') or False,
                    'emergency_phone': kw.get('emergency_phone') or False,
                    'study_field': kw.get('study_field') or False,
                    'study_school': kw.get('study_school') or False,
                    'spouse_complete_name': kw.get('spouse_complete_name') or False,
                }
                if kw.get('marital'):
                    emp_vals['marital'] = kw.get('marital')
                if kw.get('certificate'):
                    emp_vals['certificate'] = kw.get('certificate')
                if kw.get('children') is not None and str(kw.get('children')).strip() != '':
                    emp_vals['children'] = int(kw.get('children'))
                if kw.get('spouse_birthdate'):
                    emp_vals['spouse_birthdate'] = kw.get('spouse_birthdate')
                emp.sudo().write(emp_vals)
        except (UserError, ValidationError) as e:
            return {'error': str(e)}
        return {'success': True}

    @route('/ess/account/countries', type='json', auth='user')
    def account_countries(self):
        countries = request.env['res.country'].sudo().search([], order='name asc')
        return [{'id': c.id, 'name': c.name} for c in countries]

    @route('/ess/account/upload_avatar', type='http', auth='user', methods=['POST'], csrf=False)
    def account_upload_avatar(self, avatar=None):
        if not avatar:
            return request.make_json_response({'error': 'No file uploaded.'}, status=400)
        allowed = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        if avatar.content_type not in allowed:
            return request.make_json_response({'error': 'Invalid file type. Use JPG, PNG, GIF, or WebP.'}, status=400)
        data = avatar.read()
        if len(data) > 5 * 1024 * 1024:
            return request.make_json_response({'error': 'File too large. Maximum 5 MB.'}, status=400)
        image_b64 = base64.b64encode(data)
        partner = request.env.user.partner_id
        emp = self._get_employee_by_email()
        try:
            partner.sudo().write({'image_1920': image_b64})
            if emp:
                emp.sudo().write({'image_1920': image_b64})
        except (UserError, ValidationError) as e:
            return request.make_json_response({'error': str(e)}, status=500)
        url = f'/web/image/res.partner/{partner.id}/image_128?t={int(time.time())}'
        return request.make_json_response({'success': True, 'avatar_url': url})
