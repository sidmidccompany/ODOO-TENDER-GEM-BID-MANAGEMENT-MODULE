# controllers/api.py
import logging
import json
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)

class TenderAPIController(http.Controller):
    @http.route('/api/tender/authenticate', type='json', auth='none', csrf=False, methods=['POST'])
    def authenticate(self, **kw):
        """Authenticate API user and return token"""
        try:
            db = kw.get('db')
            login = kw.get('login')
            password = kw.get('password')
            
            if not db or not login or not password:
                return {'error': 'Missing required parameters (db, login, password)'}
            
            # Authenticate user
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return {'error': 'Authentication failed'}
            
            # Check if user has access to tender management
            user = request.env['res.users'].sudo().browse(uid)
            tender_group = request.env.ref('tender_management.group_tender_user', False)
            if not tender_group or tender_group.id not in user.groups_id.ids:
                return {'error': 'User does not have access to tender management'}
            
            # Generate token
            token = request.env['tender.api.token'].sudo().create({
                'user_id': uid,
                'name': f"API Token for {user.name}"
            })
            
            return {
                'success': True,
                'uid': uid,
                'token': token.token,
                'user_name': user.name,
                'company_id': user.company_id.id,
                'company_name': user.company_id.name
            }
        except Exception as e:
            _logger.exception("API authentication error: %s", str(e))
            return {'error': str(e)}
    
    def _validate_token(self, token):
        """Validate API token and return user_id or False"""
        if not token:
            return False
        
        token_record = request.env['tender.api.token'].sudo().search([
            ('token', '=', token),
            ('is_active', '=', True)
        ], limit=1)
        
        if not token_record:
            return False
        
        # Update last usage
        token_record.update_last_used()
        
        return token_record.user_id.id
    
    @http.route('/api/tender/tenders', type='json', auth='none', csrf=False, methods=['GET'])
    def get_tenders(self, **kw):
        """Get list of tenders"""
        try:
            token = kw.get('token') or request.httprequest.headers.get('X-API-Token')
            user_id = self._validate_token(token)
            if not user_id:
                return {'error': 'Invalid or missing API token'}
            
            # Set user context
            request.uid = user_id
            
            # Pagination
            limit = int(kw.get('limit', 50))
            offset = int(kw.get('offset', 0))
            
            # Filtering
            domain = []
            if 'state' in kw:
                domain.append(('state', '=', kw.get('state')))
            if 'tender_type' in kw:
                domain.append(('tender_type', '=', kw.get('tender_type')))
            if 'department_id' in kw:
                domain.append(('department_id', '=', int(kw.get('department_id'))))
            
            # Get tenders
            tenders = request.env['tender.tender'].search(domain, limit=limit, offset=offset)
            total_count = request.env['tender.tender'].search_count(domain)
            
            # Prepare result
            result = []
            for tender in tenders:
                result.append({
                    'id': tender.id,
                    'name': tender.name,
                    'title': tender.title,
                    'state': tender.state,
                    'tender_type': tender.tender_type,
                    'submission_date': tender.submission_date.isoformat() if tender.submission_date else False,
                    'tender_value': tender.tender_value,
                    'department_id': tender.department_id.id if tender.department_id else False,
                    'department_name': tender.department_id.name if tender.department_id else False,
                    'user_id': tender.user_id.id if tender.user_id else False,
                    'user_name': tender.user_id.name if tender.user_id else False,
                })
            
            return {
                'success': True,
                'count': len(result),
                'total': total_count,
                'data': result
            }
        except Exception as e:
            _logger.exception("API get tenders error: %s", str(e))
            return {'error': str(e)}
    
    @http.route('/api/tender/tender/<int:tender_id>', type='json', auth='none', csrf=False, methods=['GET'])
    def get_tender(self, tender_id, **kw):
        """Get tender details"""
        try:
            token = kw.get('token') or request.httprequest.headers.get('X-API-Token')
            user_id = self._validate_token(token)
            if not user_id:
                return {'error': 'Invalid or missing API token'}
            
            # Set user context
            request.uid = user_id
            
            # Get tender
            tender = request.env['tender.tender'].browse(tender_id)
            if not tender.exists():
                return {'error': 'Tender not found'}
            
            # Prepare documents
            documents = []
            for doc in tender.document_ids:
                documents.append({
                    'id': doc.id,
                    'name': doc.name,
                    'document_type': doc.document_type,
                    'date': doc.date.isoformat() if doc.date else False,
                    'is_processed_by_ocr': doc.is_processed_by_ocr,
                })
            
            # Prepare bids
            bids = []
            for bid in tender.bid_ids:
                bids.append({
                    'id': bid.id,
                    'name': bid.name,
                    'state': bid.state,
                    'technical_score': bid.technical_score,
                    'financial_bid': bid.financial_bid,
                    'creation_date': bid.creation_date.isoformat() if bid.creation_date else False,
                    'submission_date': bid.submission_date.isoformat() if bid.submission_date else False,
                })
            
            # Prepare result
            result = {
                'id': tender.id,
                'name': tender.name,
                'title': tender.title,
                'description': tender.description,
                'state': tender.state,
                'tender_type': tender.tender_type,
                'submission_date': tender.submission_date.isoformat() if tender.submission_date else False,
                'publication_date': tender.publication_date.isoformat() if tender.publication_date else False,
                'opening_date': tender.opening_date.isoformat() if tender.opening_date else False,
                'clarification_date': tender.clarification_date.isoformat() if tender.clarification_date else False,
                'tender_value': tender.tender_value,
                'bid_security': tender.bid_security,
                'emd_required': tender.emd_required,
                'emd_amount': tender.emd_amount,
                'issuing_authority': tender.issuing_authority,
                'source_url': tender.source_url,
                'department_id': tender.department_id.id if tender.department_id else False,
                'department_name': tender.department_id.name if tender.department_id else False,
                'user_id': tender.user_id.id if tender.user_id else False,
                'user_name': tender.user_id.name if tender.user_id else False,
                'team_id': tender.team_id.id if tender.team_id else False,
                'team_name': tender.team_id.name if tender.team_id else False,
                'documents': documents,
                'bids': bids,
            }
            
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            _logger.exception("API get tender error: %s", str(e))
            return {'error': str(e)}
    
    @http.route('/api/tender/tender', type='json', auth='none', csrf=False, methods=['POST'])
    def create_tender(self, **kw):
        """Create a new tender"""
        try:
            token = kw.get('token') or request.httprequest.headers.get('X-API-Token')
            user_id = self._validate_token(token)
            if not user_id:
                return {'error': 'Invalid or missing API token'}
            
            # Set user context
            request.uid = user_id
            
            # Check if user has manager rights
            user = request.env['res.users'].browse(user_id)
            tender_manager_group = request.env.ref('tender_management.group_tender_manager', False)
            if not tender_manager_group or tender_manager_group.id not in user.groups_id.ids:
                return {'error': 'User does not have manager rights to create tenders'}
            
            # Prepare tender data
            tender_data = {
                'name': kw.get('name', 'New'),
                'title': kw.get('title'),
                'description': kw.get('description'),
                'tender_type': kw.get('tender_type', 'open'),
                'state': 'draft',
                'user_id': user_id,
            }
            
            # Optional fields
            if 'department_id' in kw:
                tender_data['department_id'] = int(kw.get('department_id'))
            if 'submission_date' in kw:
                tender_data['submission_date'] = kw.get('submission_date')
            if 'publication_date' in kw:
                tender_data['publication_date'] = kw.get('publication_date')
            if 'opening_date' in kw:
                tender_data['opening_date'] = kw.get('opening_date')
            if 'tender_value' in kw:
                tender_data['tender_value'] = float(kw.get('tender_value'))
            if 'issuing_authority' in kw:
                tender_data['issuing_authority'] = kw.get('issuing_authority')
            if 'source_url' in kw:
                tender_data['source_url'] = kw.get('source_url')
            if 'team_id' in kw:
                tender_data['team_id'] = int(kw.get('team_id'))
            
            # Create tender
            tender = request.env['tender.tender'].create(tender_data)
            
            return {
                'success': True,
                'id': tender.id,
                'name': tender.name
            }
        except Exception as e:
            _logger.exception("API create tender error: %s", str(e))
            return {'error': str(e)}
    
    @http.route('/api/tender/document/upload', type='http', auth='none', csrf=False, methods=['POST'])
    def upload_document(self, **kw):
        """Upload document to a tender"""
        try:
            token = kw.get('token') or request.httprequest.headers.get('X-API-Token')
            user_id = self._validate_token(token)
            if not user_id:
                response = {'error': 'Invalid or missing API token'}
                return json.dumps(response)
            
            # Set user context
            request.uid = user_id
            
            # Check required parameters
            tender_id = kw.get('tender_id')
            document_name = kw.get('name')
            document_type = kw.get('document_type', 'other')
            
            if not tender_id or not document_name:
                response = {'error': 'Missing required parameters (tender_id, name)'}
                return json.dumps(response)
            
            # Get uploaded file
            if 'file' not in request.httprequest.files:
                response = {'error': 'No file uploaded'}
                return json.dumps(response)
            
            file = request.httprequest.files.get('file')
            if not file:
                response = {'error': 'Empty file'}
                return json.dumps(response)
            
            # Check if tender exists
            tender = request.env['tender.tender'].browse(int(tender_id))
            if not tender.exists():
                response = {'error': 'Tender not found'}
                return json.dumps(response)
            
            # Create document
            document = request.env['tender.document'].create({
                'tender_id': tender.id,
                'name': document_name,
                'document_type': document_type,
                'file': file.read(),
                'file_name': file.filename,
                'date': fields.Date.today(),
                'user_id': user_id,
                'is_public': kw.get('is_public') == '1',
            })
            
            response = {
                'success': True,
                'id': document.id,
                'name': document.name
            }
            return json.dumps(response)
        except Exception as e:
            _logger.exception("API upload document error: %s", str(e))
            response = {'error': str(e)}
            return json.dumps(response)
