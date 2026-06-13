from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from collections import OrderedDict
import base64
from odoo.osv.expression import OR


class InductionPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        
        if 'induction_count' in counters:
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
            if employee:
                induction_count = request.env['hr.induction.department.line'].sudo().search_count([
                    ('induction_id.employee_id', '=', employee.id)
                ])
                values['induction_count'] = induction_count
        
        return values

    @http.route(['/my/inductions', '/my/inductions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_inductions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kw):
        values = self._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        
        if not employee:
            return request.redirect('/my')
        
        InductionLine = request.env['hr.induction.department.line'].sudo()
        
        domain = [('induction_id.employee_id', '=', employee.id)]
        
        # Search
        if search and search_in:
            search_domain = []
            if search_in in ('induction', 'all'):
                search_domain = OR([search_domain, [('induction_id.name', 'ilike', search)]])
            if search_in in ('department', 'all'):
                search_domain = OR([search_domain, [('department_id.name', 'ilike', search)]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [('stage_id.name', 'ilike', search)]])
            domain += search_domain
        
        # Count for pager
        induction_count = InductionLine.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/inductions",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search': search, 'search_in': search_in},
            total=induction_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        if sortby == 'date':
            order = 'induction_datetime_from asc'
        elif sortby == 'name':
            order = 'induction_id.name asc'
        else:
            order = 'induction_datetime_from desc'
            
        inductions = InductionLine.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'inductions': inductions,
            'page_name': 'induction',
            'pager': pager,
            'default_url': '/my/inductions',
            'searchbar_sortings': {
                'date': {'label': _('Date'), 'order': 'induction_datetime_from asc'},
                'name': {'label': _('Name'), 'order': 'induction_id.name asc'},
            },
            'searchbar_inputs': {
                'induction': {'input': 'induction', 'label': _('Search in Inductions')},
                'department': {'input': 'department', 'label': _('Search in Departments')},
                'stage': {'input': 'stage', 'label': _('Search in Stages')},
                'all': {'input': 'all', 'label': _('Search in All')},
            },
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        
        return request.render("hr_recruitment_extended.portal_my_inductions", values)
    
    @http.route(['/my/induction/<int:induction_id>'], type='http', auth="user", website=True)
    def portal_my_induction(self, induction_id=None, **kw):
        induction = request.env['hr.induction.department.line'].sudo().browse(induction_id)
        
        if not induction or induction.induction_id.employee_id.user_id.id != request.env.user.id:
            return request.redirect('/my/inductions')
        
        values = {
            'induction': induction,
            'page_name': 'induction',
        }
        
        return request.render("hr_recruitment_extended.portal_my_induction", values)
    
    @http.route(['/my/induction/feedback'], type='http', auth="user", website=True, methods=['POST'])
    def portal_submit_feedback(self, **kw):
        induction_id = int(kw.get('induction_id', 0))
        induction = request.env['hr.induction.department.line'].sudo().browse(induction_id)
        
        if not induction or induction.induction_id.employee_id.user_id.id != request.env.user.id:
            return request.redirect('/my/inductions')
        
        feedback = kw.get('feedback')
        if feedback:
            induction.write({'remarks': feedback})
        
        # Handle attachments
        attachments = request.httprequest.files.getlist('attachment')
        attachment_ids = []
        
        if attachments:
            for attachment in attachments:
                if attachment.filename:
                    file_data = attachment.read()
                    attachment_id = request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        'datas': base64.b64encode(file_data),
                        'res_model': 'hr.induction.department.line',
                        'res_id': induction.id,
                    })
                    attachment_ids.append(attachment_id.id)
            
            if attachment_ids:
                induction.write({'attachment_ids': [(4, attachment_id) for attachment_id in attachment_ids]})
        
        return request.redirect('/my/induction/%s' % induction_id)