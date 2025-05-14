# -*- coding: utf-8 -*-

import json
import logging
import requests
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from . import gem_mappings

_logger = logging.getLogger(__name__)

class GemAPIClient:
    """
    Client for interacting with the Government e-Marketplace (GeM) API.
    This class handles all API communications with the GeM portal.
    """
    
    def __init__(self, env, config=None):
        """
        Initialize the GeM API client.
        
        Args:
            env: Odoo environment
            config: Configuration dictionary with API credentials
        """
        self.env = env
        self.config = config or {}
        self.token = None
        self.token_expiry = None
        
        # Load configuration if not provided
        if not self.config:
            ICP = self.env['ir.config_parameter'].sudo()
            self.config = {
                'gem_api_url': ICP.get_param('tender_management.gem_api_url', 'https://bidplus-integration.gem.gov.in/api/v1'),
                'gem_username': ICP.get_param('tender_management.gem_username', ''),
                'gem_password': ICP.get_param('tender_management.gem_password', ''),
                'gem_client_id': ICP.get_param('tender_management.gem_client_id', ''),
                'gem_client_secret': ICP.get_param('tender_management.gem_client_secret', ''),
            }
            
            # Check if credentials are set
            if not all([self.config['gem_username'], self.config['gem_password'], 
                         self.config['gem_client_id'], self.config['gem_client_secret']]):
                _logger.warning("GeM API credentials not fully configured")

    def _check_auth(self):
        """
        Check if authentication token is valid, refresh if needed.
        
        Returns:
            bool: True if authenticated successfully
        """
        if not self.token or not self.token_expiry or datetime.now() >= self.token_expiry:
            return self.authenticate()
        return True
            
    def authenticate(self):
        """
        Authenticate with the GeM API and get access token.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            auth_url = f"{self.config['gem_api_url']}/auth/token"
            payload = {
                'grant_type': 'password',
                'client_id': self.config['gem_client_id'],
                'client_secret': self.config['gem_client_secret'],
                'username': self.config['gem_username'],
                'password': self.config['gem_password'],
            }
            
            response = requests.post(auth_url, data=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                # Set token expiry (usually 1 hour)
                expires_in = data.get('expires_in', 3600)
                self.token_expiry = datetime.now().timestamp() + expires_in
                _logger.info("Successfully authenticated with GeM API")
                return True
            else:
                _logger.error(f"GeM API authentication failed: {response.text}")
                return False
        except Exception as e:
            _logger.exception(f"Exception during GeM API authentication: {e}")
            return False
    
    def _make_request(self, method, endpoint, data=None, params=None, files=None):
        """
        Make an API request to GeM.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data (for POST/PUT)
            params: Query parameters
            files: Files to upload
            
        Returns:
            dict: Response data
        """
        if not self._check_auth():
            raise UserError(_("Failed to authenticate with GeM API. Please check your credentials."))
            
        url = f"{self.config['gem_api_url']}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f"Bearer {self.token}",
            'Accept': 'application/json',
        }
        
        if not files and data and method in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data)
        
        try:
            response = requests.request(
                method, 
                url, 
                headers=headers,
                params=params,
                data=data,
                files=files,
                timeout=60
            )
            
            # Handle response
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_msg = f"GeM API error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise UserError(_(error_msg))
                
        except requests.exceptions.RequestException as e:
            _logger.exception(f"Request exception: {e}")
            raise UserError(_("Network error while connecting to GeM API: %s") % str(e))
        except json.JSONDecodeError:
            _logger.exception("Invalid JSON response from GeM API")
            raise UserError(_("Invalid response from GeM API"))
        except Exception as e:
            _logger.exception(f"Unexpected error: {e}")
            raise UserError(_("Unexpected error: %s") % str(e))
    
    # Public API methods
    def search_tenders(self, filters=None):
        """
        Search for tenders on GeM.
        
        Args:
            filters: Dictionary of search filters
            
        Returns:
            list: List of tender dictionaries
        """
        endpoint = "/bids/search"
        params = filters or {}
        result = self._make_request('GET', endpoint, params=params)
        
        # Map the GeM tender fields to Odoo fields
        mapped_tenders = []
        if result and 'bids' in result:
            for tender in result['bids']:
                mapped_tender = gem_mappings.map_gem_tender_to_odoo(tender)
                mapped_tenders.append(mapped_tender)
                
        return mapped_tenders
    
    def get_tender_details(self, gem_bid_id):
        """
        Get detailed information about a specific tender.
        
        Args:
            gem_bid_id: GeM bid ID
            
        Returns:
            dict: Tender details
        """
        endpoint = f"/bids/{gem_bid_id}"
        result = self._make_request('GET', endpoint)
        
        if result and 'bid' in result:
            return gem_mappings.map_gem_tender_to_odoo(result['bid'], detailed=True)
        return {}
    
    def submit_bid(self, tender_application):
        """
        Submit a bid for a tender on GeM.
        
        Args:
            tender_application: tender.application record
            
        Returns:
            dict: Submission response
        """
        endpoint = "/bids/submit"
        
        # Get tender details from the application
        tender_bid = tender_application.bid_id
        
        # Map Odoo data to GeM expected format
        gem_data = gem_mappings.map_odoo_application_to_gem(tender_application)
        
        # Submit the bid
        result = self._make_request('POST', endpoint, data=gem_data)
        
        return result
    
    def get_bid_status(self, gem_bid_id, application_ref=None):
        """
        Check the status of a submitted bid.
        
        Args:
            gem_bid_id: GeM bid ID
            application_ref: Application reference ID
            
        Returns:
            dict: Status information
        """
        params = {'bid_id': gem_bid_id}
        if application_ref:
            params['application_ref'] = application_ref
            
        endpoint = "/bids/status"
        result = self._make_request('GET', endpoint, params=params)
        
        return result
    
    def download_tender_document(self, document_id):
        """
        Download a tender document from GeM.
        
        Args:
            document_id: Document ID
            
        Returns:
            bytes: Document content
        """
        endpoint = f"/documents/{document_id}/download"
        response = self._make_request('GET', endpoint)
        
        return response.get('document_content')
    
    def upload_document(self, tender_document):
        """
        Upload a document to GeM.
        
        Args:
            tender_document: tender.document record
            
        Returns:
            dict: Upload response
        """
        endpoint = "/documents/upload"
        
        # Prepare file for upload
        document_datas = tender_document.file_content
        files = {
            'file': (tender_document.name, document_datas, tender_document.mimetype)
        }
        
        # Prepare metadata
        data = {
            'bid_id': tender_document.bid_id.gem_bid_id,
            'document_type': tender_document.type,
            'description': tender_document.description or '',
        }
        
        result = self._make_request('POST', endpoint, data=data, files=files)
        
        return result
