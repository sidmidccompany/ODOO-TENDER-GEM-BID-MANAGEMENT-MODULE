# controllers/portal.py
import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR

_logger = logging.getLogger(__name__)

class TenderPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        """Add tender menu entries to the portal layout"""
        values = super()._prepare_portal_layout_values()
        
        # Count public tenders
        public_tender_count = request.env['tender.tender'].search_count([
            ('state', 'not in', ['canceled']),
            ('document_ids.is_public', '=', True)
        ])
        values['tender_count'] = public_tender_count
        
        return values
    
    def _tender_get_searchbar_sortings(self):
        """Define sorting options for tenders"""
        return {
            'date': {'label': _('Submission Date'), 'order': 'submission_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
    
    def _tender_get_searchbar_groupby(self):
        """Define grouping options for tenders"""
        return {
            'none': {'label': _('None'), 'domain': []},
            'state': {'label': _('Status'), 'domain': [], 'order': 'state'},
        }
    
    def _tender_get_searchbar_inputs(self):
        """Define search inputs for tenders"""
        return {
            'name': {'label': _('Reference'), 'input': 'name', 'domain': [('name', 'ilike', 'name')]},
            'title': {'label': _('Title'), 'input': 'title', 'domain': [('title', 'ilike', 'title')]},
        }
    
    @http.route(['/my/tenders', '/my/tenders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tenders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='name', groupby=None, **kw):
        """Portal page to display list of tenders"""
        values = self._prepare_portal_layout_values()
        
        # Define default domain
        domain = [
            ('state', 'not in', ['canceled']),
            ('document_ids.is_public', '=', True)
        ]
        
        searchbar_sortings = self._tender_get_searchbar_sortings()
        searchbar_groupby = self._tender_get_searchbar_groupby()
        searchbar_inputs = self._tender_get_searchbar_inputs()
        
        # Default sort by submission date
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Default group by none
        if not groupby:
            groupby = 'none'
        
        # Search
        if search and search_in:
            search_domain = []
            if search_in == 'name':
                search_domain = [('name', 'ilike', search)]
            elif search_in == 'title':
                search_domain = [('title', 'ilike', search)]
            domain = AND([domain, search_domain])
        
        # Count for pager
        tender_count = request.env['tender.tender'].search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/tenders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            total=tender_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content according to pager and archive selected
        if groupby == 'state':
            # Force sort by state
            order = 'state, %s' % order
        
        tenders = request.env['tender.tender'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        if groupby == 'state':
            grouped_tenders = [request.env['tender.tender'].concat(*g) for k, g in groupbyelem(tenders, itemgetter('state'))]
        else:
            grouped_tenders = [tenders]
        
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_tenders': grouped_tenders,
            'page_name': 'tender',
            'default_url': '/my/tenders',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'groupby': groupby,
            'search': search,
        })
        
        return request.render("tender_management.portal_my_tenders", values)
    
    @http.route(['/my/tender/<int:tender_id>'], type='http', auth="user", website=True)
    def portal_my_tender(self, tender_id=None, access_token=None, **kw):
        """Display a specific tender on the portal"""
        try:
            tender_sudo = self._document_check_access('tender.tender', tender_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # Check if tender has public documents
        if not tender_sudo.document_ids.filtered(lambda d: d.is_public):
            return request.redirect('/my')
        
        values = self._tender_get_page_view_values(tender_sudo, access_token, **kw)
        return request.render("tender_management.portal_my_tender", values)
    
    @http.route(['/my/tender/<int:tender_id>/document/<int:document_id>'], type='http', auth="user", website=True)
    def portal_tender_document(self, tender_id=None, document_id=None, access_token=None, **kw):
        """Download a tender document from the portal"""
        try:
            tender_sudo = self._document_check_access('tender.tender', tender_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # Check if document exists and is public
        document = request.env['tender.document'].sudo().search([
            ('id', '=', document_id),
            ('tender_id', '=', tender_id),
            ('is_public', '=', True)
        ], limit=1)
        
        if not document:
            return request.redirect('/my')
        
        # Return the file as an attachment
        return http.request.make_response(
            document.file,
            [
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', 'attachment; filename="%s"' % document.file_name)
            ]
        )
