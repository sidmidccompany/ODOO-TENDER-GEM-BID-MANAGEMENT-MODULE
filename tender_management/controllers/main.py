# controllers/main.py
import logging
import json
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)

class TenderController(http.Controller):
    @http.route('/tender/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self, **kw):
        """Get dashboard data for the current user"""
        result = request.env['tender.tender'].get_dashboard_data()
        return result
    
    @http.route('/tender/ai/chat', type='json', auth='user')
    def ai_chat(self, tender_id, message, **kw):
        """Process AI chat messages"""
        try:
            tender = request.env['tender.tender'].browse(int(tender_id))
            if not tender.exists():
                return {'error': _("Tender not found")}
            
            result = tender.get_ai_assistant_response(message)
            return result
        except Exception as e:
            _logger.exception("Error in AI chat: %s", str(e))
            return {'error': _("An error occurred while processing your request")}
    
    @http.route('/tender/analytics/data/<int:tender_id>', type='json', auth='user')
    def get_analytics_data(self, tender_id, **kw):
        """Get analytics data for a specific tender"""
        try:
            tender = request.env['tender.tender'].browse(tender_id)
            if not tender.exists():
                return {'error': _("Tender not found")}
            
            if not tender.analytics_id:
                return {'error': _("No analytics data available for this tender")}
            
            return json.loads(tender.analytics_id.data_json or '{}')
        except Exception as e:
            _logger.exception("Error getting analytics data: %s", str(e))
            return {'error': _("An error occurred while getting analytics data")}
    
    @http.route('/tender/ocr/process/<int:document_id>', type='json', auth='user')
    def process_ocr(self, document_id, **kw):
        """Process a document with OCR"""
        try:
            document = request.env['tender.document'].browse(document_id)
            if not document.exists():
                return {'error': _("Document not found")}
            
            if document.is_processed_by_ocr:
                return {'error': _("This document has already been processed with OCR")}
            
            # Create OCR record
            ocr_result = request.env['tender.ocr'].create({
                'document_id': document.id,
                'tender_id': document.tender_id.id,
                'state': 'draft'
            })
            
            # Process OCR
            ocr_result.action_process()
            
            # Update document
            document.write({
                'is_processed_by_ocr': True,
                'ocr_result_id': ocr_result.id
            })
            
            return {
                'success': True,
                'ocr_id': ocr_result.id,
                'state': ocr_result.state
            }
        except Exception as e:
            _logger.exception("Error in OCR processing: %s", str(e))
            return {'error': _("An error occurred during OCR processing")}
    
    @http.route('/tender/tag/create', type='json', auth='user')
    def create_tag(self, name, color=0, **kw):
        """Create a new tag"""
        try:
            if not name:
                return {'error': _("Tag name cannot be empty")}
            
            # Check if tag already exists
            existing_tag = request.env['tender.tag'].search([('name', '=', name)], limit=1)
            if existing_tag:
                return {
                    'success': False,
                    'tag_id': existing_tag.id,
                    'error': _("Tag already exists")
                }
            
            # Create new tag
            tag = request.env['tender.tag'].create({
                'name': name,
                'color': color
            })
            
            return {
                'success': True,
                'tag_id': tag.id
            }
        except Exception as e:
            _logger.exception("Error creating tag: %s", str(e))
            return {'error': _("An error occurred while creating the tag")}


class TenderCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        """Add tender counts to portal home page"""
        values = super()._prepare_home_portal_values(counters)
        
        if 'tender_count' in counters:
            tender_count = request.env['tender.tender'].search_count([
                ('state', 'not in', ['canceled']),
                ('document_ids.is_public', '=', True)
            ])
            values['tender_count'] = tender_count
        
        return values
    
    def _tender_get_page_view_values(self, tender, access_token, **kwargs):
        """Prepare values for rendering portal pages for a tender"""
        values = {
            'tender': tender,
            'page_name': 'tender',
            'user': request.env.user,
        }
        
        # Get public documents
        values['documents'] = request.env['tender.document'].search([
            ('tender_id', '=', tender.id),
            ('is_public', '=', True)
        ])
        
        return self._get_page_view_values(
            tender, access_token, values, 'my_tenders_history', False, **kwargs
        )
