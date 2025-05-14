# models/gem_portal.py
import logging
import requests
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class GemPortal(models.Model):
    _name = 'gem.portal'
    _description = 'GeM Portal Integration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Portal Name', required=True)
    api_endpoint = fields.Char(string='API Endpoint', required=True)
    api_key = fields.Char(string='API Key', required=True, groups="tender_management.group_tender_admin")
    api_secret = fields.Char(string='API Secret', required=True, groups="tender_management.group_tender_admin")
    active = fields.Boolean(default=True)
    
    # Connection Status
    last_connection = fields.Datetime(string='Last Connection')
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('failed', 'Connection Failed'),
        ('not_tested', 'Not Tested')
    ], string='Connection Status', default='not_tested', tracking=True)
    
    # Related Tenders
    tender_count = fields.Integer(compute='_compute_tender_count')
    bid_count = fields.Integer(compute='_compute_bid_count')
    
    # Technical Fields
    token = fields.Char(string='Access Token', groups="tender_management.group_tender_admin")
    token_expiry = fields.Datetime(string='Token Expiry')
    
    @api.depends('tender_ids')
    def _compute_tender_count(self):
        for portal in self:
            portal.tender_count = self.env['tender.tender'].search_count([
                ('gem_portal_id', '=', portal.id)
            ])
    
    @api.depends('bid_ids')
    def _compute_bid_count(self):
        for portal in self:
            portal.bid_count = self.env['gem.bid'].search_count([
                ('gem_portal_id', '=', portal.id)
            ])
    
    def action_test_connection(self):
        """Test the connection to the GeM Portal"""
        self.ensure_one()
        try:
            # Try to get auth token
            token = self._get_token()
            if token:
                self.write({
                    'connection_status': 'connected',
                    'last_connection': fields.Datetime.now(),
                    'token': token['access_token'],
                    'token_expiry': datetime.fromtimestamp(token['expires_at'])
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Successfully connected to GeM Portal.'),
                        'sticky': False,
                    }
                }
            else:
                self.write({
                    'connection_status': 'failed',
                    'last_connection': fields.Datetime.now(),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _('Failed to connect to GeM Portal. Could not obtain token.'),
                        'sticky': False,
                        'type': 'danger'
                    }
                }
        except Exception as e:
            self.write({
                'connection_status': 'failed',
                'last_connection': fields.Datetime.now(),
            })
            _logger.error("GeM Portal connection error: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to connect to GeM Portal: %s') % str(e),
                    'sticky': False,
                    'type': 'danger'
                }
            }
    
    def _get_token(self):
        """Get authentication token from GeM Portal"""
        self.ensure_one()
        
        # Check if we already have a valid token
        if self.token and self.token_expiry and self.token_expiry > fields.Datetime.now():
            return {
                'access_token': self.token,
                'expires_at': self.token_expiry.timestamp()
            }
        
        # Otherwise, get a new token
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            data = {
                'apiKey': self.api_key,
                'secret': self.api_secret
            }
            
            response = requests.post(
                f"{self.api_endpoint}/auth/token",
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                _logger.error(
                    "Failed to get token from GeM Portal. Status code: %s, Response: %s",
                    response.status_code, response.text
                )
                return None
        except Exception as e:
            _logger.error("Error getting token from GeM Portal: %s", str(e))
            return None
    
    def fetch_tender_details(self, tender):
        """Fetch tender details from GeM Portal"""
        self.ensure_one()
        if not tender.gem_bid_id:
            raise UserError(_("GeM Bid ID must be set to fetch tender details"))
        
        token = self._get_token()
        if not token:
            raise UserError(_("Failed to authenticate with GeM Portal"))
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {token['access_token']}"
            }
            
            response = requests.get(
                f"{self.api_endpoint}/tenders/{tender.gem_bid_id}",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                tender_data = response.json()
                self._update_tender_from_gem_data(tender, tender_data)
                return True
            else:
                _logger.error(
                    "Failed to fetch tender details from GeM Portal. Status code: %s, Response: %s",
                    response.status_code, response.text
                )
                raise UserError(_("Failed to fetch tender details: %s") % response.text)
        except Exception as e:
            _logger.error("Error fetching tender details from GeM Portal: %s", str(e))
            raise UserError(_("Error fetching tender details: %s") % str(e))
    
    def _update_tender_from_gem_data(self, tender, data):
        """Update tender with data from GeM Portal"""
        if not data:
            return
        
        # Update tender fields with GeM data
        tender.write({
            'title': data.get('title', tender.title),
            'description': data.get('description', tender.description),
            'submission_date': datetime.strptime(data.get('submissionDate'), '%Y-%m-%dT%H:%M:%S') if data.get('submissionDate') else tender.submission_date,
            'publication_date': datetime.strptime(data.get('publicationDate'), '%Y-%m-%dT%H:%M:%S') if data.get('publicationDate') else tender.publication_date,
            'opening_date': datetime.strptime(data.get('openingDate'), '%Y-%m-%dT%H:%M:%S') if data.get('openingDate') else tender.opening_date,
            'tender_value': float(data.get('estimatedValue', 0.0)),
            'bid_security': float(data.get('bidSecurityAmount', 0.0)),
            'emd_required': bool(data.get('emdRequired', False)),
            'emd_amount': float(data.get('emdAmount', 0.0)),
            'issuing_authority': data.get('issuingAuthority', tender.issuing_authority),
            'source_url': data.get('sourceUrl', tender.source_url),
        })
        
        # Create documents if they exist in the response
        if 'documents' in data and isinstance(data['documents'], list):
            for doc_data in data['documents']:
                # Check if document already exists
                existing_doc = self.env['tender.document'].search([
                    ('tender_id', '=', tender.id),
                    ('name', '=', doc_data.get('name'))
                ], limit=1)
                
                if not existing_doc:
                    # Download the document
                    doc_content = self._download_document(doc_data.get('url'))
                    if doc_content:
                        self.env['tender.document'].create({
                            'tender_id': tender.id,
                            'name': doc_data.get('name'),
                            'document_type': self._map_document_type(doc_data.get('type')),
                            'description': doc_data.get('description'),
                            'file': doc_content,
                            'file_name': doc_data.get('name'),
                            'date': datetime.strptime(doc_data.get('date'), '%Y-%m-%d').date() if doc_data.get('date') else fields.Date.today(),
                        })
    
    def _download_document(self, url):
        """Download document from URL"""
        if not url:
            return None
        
        token = self._get_token()
        if not token:
            _logger.error("Failed to authenticate with GeM Portal to download document")
            return None
        
        try:
            headers = {
                'Authorization': f"Bearer {token['access_token']}"
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                _logger.error(
                    "Failed to download document from GeM Portal. Status code: %s",
                    response.status_code
                )
                return None
        except Exception as e:
            _logger.error("Error downloading document from GeM Portal: %s", str(e))
            return None
    
    def _map_document_type(self, gem_type):
        """Map GeM document type to Odoo document type"""
        mapping = {
            'TENDER_NOTICE': 'tender_notice',
            'TECHNICAL_SPECIFICATION': 'technical_specification',
            'FINANCIAL_SPECIFICATION': 'financial_specification',
            'CORRIGENDUM': 'corrigendum',
            'PRE_BID_QUERY': 'pre_bid_query',
            'BID_DOCUMENT': 'bid_document',
            'SUBMISSION': 'submission'
        }
        return mapping.get(gem_type, 'other')
    
    def action_view_tenders(self):
        """View tenders using this GeM Portal"""
        self.ensure_one()
        return {
            'name': _('Tenders'),
            'view_mode': 'tree,form',
            'res_model': 'tender.tender',
            'domain': [('gem_portal_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_gem_portal_id': self.id, 'default_tender_type': 'gem'}
        }
    
    def action_view_bids(self):
        """View bids using this GeM Portal"""
        self.ensure_one()
        return {
            'name': _('Bids'),
            'view_mode': 'tree,form',
            'res_model': 'gem.bid',
            'domain': [('gem_portal_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_gem_portal_id': self.id}
        }
    
    @api.model
    def _cron_sync_gem_tenders(self):
        """Cron job to sync tenders from GeM Portal"""
        portals = self.search([('active', '=', True)])
        for portal in portals:
            try:
                portal._sync_tenders()
            except Exception as e:
                _logger.error("Error syncing tenders from GeM Portal %s: %s", portal.name, str(e))
    
    def _sync_tenders(self):
        """Sync tenders from GeM Portal"""
        self.ensure_one()
        
        token = self._get_token()
        if not token:
            _logger.error("Failed to authenticate with GeM Portal to sync tenders")
            return
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {token['access_token']}"
            }
            
            # Get new tenders published in the last 24 hours
            response = requests.get(
                f"{self.api_endpoint}/tenders/recent",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                tenders_data = response.json()
                self._create_update_tenders(tenders_data)
            else:
                _logger.error(
                    "Failed to sync tenders from GeM Portal. Status code: %s, Response: %s",
                    response.status_code, response.text
                )
        except Exception as e:
            _logger.error("Error syncing tenders from GeM Portal: %s", str(e))
    
    def _create_update_tenders(self, tenders_data):
        """Create or update tenders from GeM data"""
        if not tenders_data or not isinstance(tenders_data, list):
            return
        
        for tender_data in tenders_data:
            gem_bid_id = tender_data.get('bidId')
            if not gem_bid_id:
                continue
            
            # Check if tender already exists
            existing_tender = self.env['tender.tender'].search([
                ('gem_bid_id', '=', gem_bid_id),
                ('gem_portal_id', '=', self.id)
            ], limit=1)
            
            if existing_tender:
                # Update existing tender
                self._update_tender_from_gem_data(existing_tender, tender_data)
            else:
                # Create new tender
                new_tender = self.env['tender.tender'].create({
                    'name': f"GeM-{gem_bid_id}",
                    'title': tender_data.get('title', ''),
                    'description': tender_data.get('description', ''),
                    'submission_date': datetime.strptime(tender_data.get('submissionDate'), '%Y-%m-%dT%H:%M:%S') if tender_data.get('submissionDate') else False,
                    'publication_date': datetime.strptime(tender_data.get('publicationDate'), '%Y-%m-%dT%H:%M:%S') if tender_data.get('publicationDate') else False,
                    'tender_value': float(tender_data.get('estimatedValue', 0.0)),
                    'issuing_authority': tender_data.get('issuingAuthority', ''),
                    'source_url': tender_data.get('sourceUrl', ''),
                    'tender_type': 'gem',
                    'gem_portal_id': self.id,
                    'gem_bid_id': gem_bid_id,
                    'state': 'draft'
                })
                
                # Update with full data
                self._update_tender_from_gem_data(new_tender, tender_data)


class GemBid(models.Model):
    _name = 'gem.bid'
    _description = 'GeM Bid'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Bid Reference', required=True)
    gem_portal_id = fields.Many2one('gem.portal', string='GeM Portal', required=True)
    tender_id = fields.Many2one('tender.tender', string='Tender', required=True)
    bid_id = fields.Char(string='GeM Bid ID', required=True)
    
    # Bid Details
    bid_value = fields.Monetary(string='Bid Value', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='tender_id.currency_id')
    technical_score = fields.Float(string='Technical Score')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_evaluation', 'Under Evaluation'),
        ('awarded', 'Awarded'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled')
    ], string='Status', default='draft', tracking=True)
    
    # Dates
    submission_date = fields.Datetime(string='Submission Date')
    award_date = fields.Datetime(string='Award Date')
    
    # Documents
    document_ids = fields.One2many('tender.document', 'gem_bid_id', string='Bid Documents')
    
    # Notes
    notes = fields.Html(string='Notes')
    
    def action_submit(self):
        """Submit the bid to GeM portal"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft bids can be submitted"))
        
        # Get token
        token = self.gem_portal_id._get_token()
        if not token:
            raise UserError(_("Failed to authenticate with GeM Portal"))
        
        try:
            # Prepare bid data
            bid_data = self._prepare_bid_data()
            
            # Submit bid to GeM
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {token['access_token']}"
            }
            
            response = requests.post(
                f"{self.gem_portal_id.api_endpoint}/bids",
                headers=headers,
                data=json.dumps(bid_data),
                timeout=30
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                self.write({
                    'state': 'submitted',
                    'submission_date': fields.Datetime.now(),
                    'bid_id': result.get('bidId', self.bid_id)
                })
                # Update tender status
                if self.tender_id.state != 'submitted':
                    self.tender_id.action_submit_bid()
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Bid successfully submitted to GeM Portal.'),
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.text or f"Error code: {response.status_code}"
                raise UserError(_("Failed to submit bid: %s") % error_msg)
        except requests.exceptions.RequestException as e:
            raise UserError(_("Network error: %s") % str(e))
        except Exception as e:
            raise UserError(_("Error submitting bid: %s") % str(e))
    
    def _prepare_bid_data(self):
        """Prepare bid data for GeM submission"""
        # Get documents to attach
        documents = []
        for doc in self.document_ids:
            doc_data = {
                'name': doc.name,
                'type': self._reverse_map_document_type(doc.document_type),
                'content': doc.file.decode('utf-8') if doc.file else None
            }
            documents.append(doc_data)
        
        # Prepare bid data
        return {
            'tenderId': self.tender_id.gem_bid_id,
            'bidValue': self.bid_value,
            'documents': documents,
            'notes': self.notes or ''
        }
    
    def _reverse_map_document_type(self, odoo_type):
        """Map Odoo document type to GeM document type"""
        mapping = {
            'tender_notice': 'TENDER_NOTICE',
            'technical_specification': 'TECHNICAL_SPECIFICATION',
            'financial_specification': 'FINANCIAL_SPECIFICATION',
            'corrigendum': 'CORRIGENDUM',
            'pre_bid_query': 'PRE_BID_QUERY',
            'bid_document': 'BID_DOCUMENT',
            'submission': 'SUBMISSION',
            'other': 'OTHER'
        }
        return mapping.get(odoo_type, 'OTHER')
    
    def action_check_status(self):
        """Check bid status from GeM Portal"""
        self.ensure_one()
        if not self.bid_id:
            raise UserError(_("No GeM Bid ID available to check status"))
        
        # Get token
        token = self.gem_portal_id._get_token()
        if not token:
            raise UserError(_("Failed to authenticate with GeM Portal"))
        
        try:
            headers = {
                'Authorization': f"Bearer {token['access_token']}"
            }
            
            response = requests.get(
                f"{self.gem_portal_id.api_endpoint}/bids/{self.bid_id}/status",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                status_data = response.json()
                self._update_status_from_gem(status_data)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Bid status successfully updated from GeM Portal.'),
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.text or f"Error code: {response.status_code}"
                raise UserError(_("Failed to check bid status: %s") % error_msg)
        except Exception as e:
            raise UserError(_("Error checking bid status: %s") % str(e))
    
    def _update_status_from_gem(self, status_data):
        """Update bid status from GeM data"""
        if not status_data:
            return
        
        # Map GeM status to Odoo status
        status_mapping = {
            'DRAFT': 'draft',
            'SUBMITTED': 'submitted',
            'UNDER_EVALUATION': 'under_evaluation',
            'AWARDED': 'awarded',
            'REJECTED': 'rejected',
            'CANCELED': 'canceled'
        }
        
        gem_status = status_data.get('status')
        odoo_status = status_mapping.get(gem_status, self.state)
        
        # Update bid fields
        values = {
            'state': odoo_status,
            'technical_score': float(status_data.get('technicalScore', 0.0)),
        }
        
        # Update award date if awarded
        if odoo_status == 'awarded' and status_data.get('awardDate'):
            values['award_date'] = datetime.strptime(status_data.get('awardDate'), '%Y-%m-%dT%H:%M:%S')
        
        self.write(values)
        
        # Update tender status
        if odoo_status == 'awarded' and self.tender_id.state != 'awarded':
            self.tender_id.action_mark_awarded()
        elif odoo_status == 'rejected' and self.tender_id.state != 'rejected':
            self.tender_id.action_mark_rejected()
    
    @api.model
    def _cron_update_gem_bid_status(self):
        """Cron job to update GeM bid statuses"""
        # Find bids with submitted state
        bids = self.search([
            ('state', 'in', ['submitted', 'under_evaluation']),
            ('gem_portal_id', '!=', False),
            ('bid_id', '!=', False)
        ])
        
        for bid in bids:
            try:
                bid.action_check_status()
            except Exception as e:
                _logger.error("Error updating bid status for bid %s: %s", bid.name, str(e))
