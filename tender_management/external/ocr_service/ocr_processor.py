# -*- coding: utf-8 -*-

import base64
import json
import logging
import requests
from io import BytesIO
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    This class handles OCR processing for tender documents.
    It integrates with OCR services to extract text and data from scanned documents.
    """
    
    def __init__(self, env):
        """
        Initialize the OCR processor.
        
        Args:
            env: Odoo environment
        """
        self.env = env
        ICP = self.env['ir.config_parameter'].sudo()
        
        # Load configuration
        self.config = {
            'ocr_service_url': ICP.get_param('tender_management.ocr_service_url', ''),
            'ocr_api_key': ICP.get_param('tender_management.ocr_api_key', ''),
            'ocr_service_provider': ICP.get_param('tender_management.ocr_service_provider', 'google_vision'),
            'ocr_enabled': ICP.get_param('tender_management.ocr_enabled', 'False') == 'True',
        }
        
        # Check if OCR is properly configured
        if not all([self.config['ocr_service_url'], self.config['ocr_api_key']]) and self.config['ocr_enabled']:
            _logger.warning("OCR service is enabled but not fully configured")
    
    def is_available(self):
        """
        Check if the OCR service is available and properly configured.
        
        Returns:
            bool: True if available
        """
        return self.config['ocr_enabled'] and all([self.config['ocr_service_url'], self.config['ocr_api_key']])
    
    def process_document(self, document):
        """
        Process a document with OCR to extract text.
        
        Args:
            document: tender.document record
            
        Returns:
            dict: OCR results including extracted text
        """
        if not self.is_available():
            raise UserError(_("OCR service is not properly configured or enabled."))
        
        # Get document data
        try:
            document_data = base64.b64decode(document.file_content)
        except Exception as e:
            _logger.error(f"Failed to decode document data: {e}")
            raise UserError(_("Invalid document data: %s") % str(e))
            
        # Select OCR service provider
        if self.config['ocr_service_provider'] == 'google_vision':
            return self._process_with_google_vision(document_data, document.mimetype)
        elif self.config['ocr_service_provider'] == 'microsoft_azure':
            return self._process_with_azure_ocr(document_data, document.mimetype)
        elif self.config['ocr_service_provider'] == 'tesseract_api':
            return self._process_with_tesseract_api(document_data, document.mimetype)
        else:
            return self._process_with_custom_ocr(document_data, document.mimetype)
    
    def _process_with_google_vision(self, document_data, mimetype):
        """
        Process document using Google Cloud Vision OCR.
        
        Args:
            document_data: Binary document data
            mimetype: Document MIME type
            
        Returns:
            dict: OCR results
        """
        try:
            endpoint = "https://vision.googleapis.com/v1/images:annotate"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.config['ocr_api_key']}"
            }
            
            # Encode image data to base64
            encoded_content = base64.b64encode(document_data).decode('utf-8')
            
            # Prepare the request payload
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": encoded_content
                        },
                        "features": [
                            {
                                "type": "DOCUMENT_TEXT_DETECTION"
                            }
                        ]
                    }
                ]
            }
            
            # Make the API request
            response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract the text from response
                if response_data.get('responses') and len(response_data['responses']) > 0:
                    text_annotations = response_data['responses'][0].get('textAnnotations', [])
                    if text_annotations:
                        full_text = text_annotations[0].get('description', '')
                        return {
                            'success': True,
                            'text': full_text,
                            'provider': 'google_vision',
                            'confidence': 0.0,  # Google doesn't provide an overall confidence score
                            'raw_response': response_data
                        }
                
                return {
                    'success': False,
                    'error': 'No text found in the document',
                    'provider': 'google_vision',
                    'raw_response': response_data
                }
            else:
                error_msg = f"Google Vision API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'provider': 'google_vision'
                }
                
        except Exception as e:
            error_msg = f"Google Vision OCR processing error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'provider': 'google_vision'
            }
    
    def _process_with_azure_ocr(self, document_data, mimetype):
        """
        Process document using Microsoft Azure OCR.
        
        Args:
            document_data: Binary document data
            mimetype: Document MIME type
            
        Returns:
            dict: OCR results
        """
        try:
            endpoint = f"{self.config['ocr_service_url']}/vision/v3.2/read/analyze"
            headers = {
                'Content-Type': mimetype,
                'Ocp-Apim-Subscription-Key': self.config['ocr_api_key']
            }
            
            # Make the initial API request
            response = requests.post(endpoint, headers=headers, data=document_data, timeout=30)
            
            if response.status_code in [200, 202]:
                # Get operation location from response header
                operation_location = response.headers.get('Operation-Location')
                if not operation_location:
                    return {
                        'success': False,
                        'error': 'No operation location found in response headers',
                        'provider': 'microsoft_azure'
                    }
                
                # Poll until processing is complete
                import time
                headers = {'Ocp-Apim-Subscription-Key': self.config['ocr_api_key']}
                for _ in range(10):  # Try 10 times with 1-second delay
                    time.sleep(1)
                    result_response = requests.get(operation_location, headers=headers, timeout=30)
                    result = result_response.json()
                    
                    if result.get('status') == 'succeeded':
                        # Extract text from the result
                        full_text = ""
                        confidence_sum = 0.0
                        confidence_count = 0
                        
                        read_results = result.get('analyzeResult', {}).get('readResults', [])
                        for read_result in read_results:
                            for line in read_result.get('lines', []):
                                full_text += line.get('text', '') + "\n"
                                if 'confidence' in line:
                                    confidence_sum += line.get('confidence', 0.0)
                                    confidence_count += 1
                        
                        avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0.0
                        
                        return {
                            'success': True,
                            'text': full_text,
                            'provider': 'microsoft_azure',
                            'confidence': avg_confidence,
                            'raw_response': result
                        }
                    
                    if result.get('status') == 'failed':
                        return {
                            'success': False,
                            'error': f"Azure OCR processing failed: {result.get('errorMessage', 'Unknown error')}",
                            'provider': 'microsoft_azure',
                            'raw_response': result
                        }
                
                return {
                    'success': False,
                    'error': 'Timeout while waiting for OCR processing to complete',
                    'provider': 'microsoft_azure'
                }
            else:
                error_msg = f"Azure OCR API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'provider': 'microsoft_azure'
                }
                
        except Exception as e:
            error_msg = f"Azure OCR processing error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'provider': 'microsoft_azure'
            }
    
    def _process_with_tesseract_api(self, document_data, mimetype):
        """
        Process document using Tesseract OCR API.
        
        Args:
            document_data: Binary document data
            mimetype: Document MIME type
            
        Returns:
            dict: OCR results
        """
        try:
            endpoint = self.config['ocr_service_url']
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.config['ocr_api_key']
            }
            
            # Encode image data to base64
            encoded_content = base64.b64encode(document_data).decode('utf-8')
            
            # Prepare the request payload
            payload = {
                "image": encoded_content,
                "mimetype": mimetype,
                "options": {
                    "lang": "eng",  # Default to English
                    "oem": 1,  # LSTM OCR Engine
                    "psm": 3,  # Auto page segmentation with OSD
                }
            }
            
            # Make the API request
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                
                return {
                    'success': response_data.get('success', False),
                    'text': response_data.get('text', ''),
                    'provider': 'tesseract_api',
                    'confidence': response_data.get('confidence', 0.0),
                    'raw_response': response_data
                }
            else:
                error_msg = f"Tesseract API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'provider': 'tesseract_api'
                }
                
        except Exception as e:
            error_msg = f"Tesseract OCR processing error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'provider': 'tesseract_api'
            }
    
    def _process_with_custom_ocr(self, document_data, mimetype):
        """
        Process document using a custom OCR service.
        
        Args:
            document_data: Binary document data
            mimetype: Document MIME type
            
        Returns:
            dict: OCR results
        """
        try:
            endpoint = self.config['ocr_service_url']
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.config['ocr_api_key']}"
            }
            
            # Encode image data to base64
            encoded_content = base64.b64encode(document_data).decode('utf-8')
            
            # Prepare the request payload
            payload = {
                "document": {
                    "content": encoded_content,
                    "mimeType": mimetype,
                },
                "options": {
                    "extractText": True,
                    "extractTables": True,
                    "extractForms": True,
                }
            }
            
            # Make the API request
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                
                return {
                    'success': True,
                    'text': response_data.get('text', ''),
                    'provider': 'custom',
                    'confidence': response_data.get('confidence', 0.0),
                    'raw_response': response_data
                }
            else:
                error_msg = f"Custom OCR API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'provider': 'custom'
                }
                
        except Exception as e:
            error_msg = f"Custom OCR processing error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'provider': 'custom'
            }
    
    def extract_key_information(self, ocr_result, document_type='general'):
        """
        Extract key information from OCR results based on document type.
        
        Args:
            ocr_result: OCR result dictionary with extracted text
            document_type: Type of document for targeted extraction
            
        Returns:
            dict: Extracted key information
        """
        if not ocr_result.get('success', False) or not ocr_result.get('text'):
            return {
                'success': False,
                'error': 'No text available for extraction'
            }
            
        extracted_text = ocr_result.get('text', '')
        
        # Basic information extraction based on document type
        if document_type == 'tender_notice':
            return self._extract_tender_notice_info(extracted_text)
        elif document_type == 'bid_document':
            return self._extract_bid_document_info(extracted_text)
        elif document_type == 'corrigendum':
            return self._extract_corrigendum_info(extracted_text)
        else:
            # Generic extraction for unknown document types
            return self._extract_generic_info(extracted_text)
    
    def _extract_tender_notice_info(self, text):
        """
        Extract information from tender notice documents.
        
        Args:
            text: Extracted OCR text
            
        Returns:
            dict: Extracted information
        """
        # Simple rule-based extraction - in a real implementation, 
        # this would use more sophisticated NLP techniques
        import re
        
        # Initialize result dictionary
        result = {
            'success': True,
            'tender_id': None,
            'tender_title': None,
            'organization': None,
            'submission_date': None,
            'closing_date': None,
            'estimated_value': None,
        }
        
        # Extract tender ID/reference
        tender_id_match = re.search(r'Tender\s+(?:ID|No|Number|Ref|Reference)\s*:?\s*([A-Z0-9-/]+)', text, re.IGNORECASE)
        if tender_id_match:
            result['tender_id'] = tender_id_match.group(1).strip()
        
        # Extract tender title
        title_match = re.search(r'(?:Title|Subject)\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if title_match:
            result['tender_title'] = title_match.group(1).strip()
        
        # Extract organization
        org_match = re.search(r'(?:Organization|Authority|Department|Ministry)\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if org_match:
            result['organization'] = org_match.group(1).strip()
        
        # Extract dates (submission, closing)
        submission_date_match = re.search(r'(?:Start|Submission|Publishing)\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', text, re.IGNORECASE)
        if submission_date_match:
            result['submission_date'] = submission_date_match.group(1).strip()
            
        closing_date_match = re.search(r'(?:End|Closing|Due)\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', text, re.IGNORECASE)
        if closing_date_match:
            result['closing_date'] = closing_date_match.group(1).strip()
        
        # Extract estimated value
        value_match = re.search(r'(?:Estimated|Approximate|Approx\.?)\s+(?:Value|Cost|Amount|Budget)\s*:?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', text, re.IGNORECASE)
        if value_match:
            # Remove commas and convert to float
            value_str = value_match.group(1).replace(',', '')
            try:
                result['estimated_value'] = float(value_str)
            except ValueError:
                pass
        
        return result
    
    def _extract_bid_document_info(self, text):
        """
        Extract information from bid documents.
        
        Args:
            text: Extracted OCR text
            
        Returns:
            dict: Extracted information
        """
        import re
        
        # Initialize result dictionary
        result = {
            'success': True,
            'bid_id': None,
            'bidder_name': None,
            'bid_amount': None,
            'submission_date': None,
            'contact_person': None,
            'contact_email': None,
            'contact_phone': None,
        }
        
        # Extract bid ID
        bid_id_match = re.search(r'(?:Bid|Tender)\s+(?:ID|No|Number|Ref|Reference)\s*:?\s*([A-Z0-9-/]+)', text, re.IGNORECASE)
        if bid_id_match:
            result['bid_id'] = bid_id_match.group(1).strip()
        
        # Extract bidder name
        bidder_match = re.search(r'(?:Bidder|Company|Vendor|Supplier)\s+Name\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if bidder_match:
            result['bidder_name'] = bidder_match.group(1).strip()
        
        # Extract bid amount
        amount_match = re.search(r'(?:Bid|Quoted|Total)\s+(?:Amount|Value|Price|Cost)\s*:?\s*(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', text, re.IGNORECASE)
        if amount_match:
            # Remove commas and convert to float
            amount_str = amount_match.group(1).replace(',', '')
            try:
                result['bid_amount'] = float(amount_str)
            except ValueError:
                pass
        
        # Extract submission date
        date_match = re.search(r'(?:Submission|Bid)\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', text, re.IGNORECASE)
        if date_match:
            result['submission_date'] = date_match.group(1).strip()
        
        # Extract contact information
        contact_person_match = re.search(r'(?:Contact|Authorized)\s+Person\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if contact_person_match:
            result['contact_person'] = contact_person_match.group(1).strip()
            
        email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        if email_match:
            result['contact_email'] = email_match.group(0)
            
        phone_match = re.search(r'(?:Phone|Mobile|Tel|Contact)\s*(?:No|Number)?\s*:?\s*(\+?\d[\d\s-]{8,})', text, re.IGNORECASE)
        if phone_match:
            result['contact_phone'] = phone_match.group(1).strip()
        
        return result
    
    def _extract_corrigendum_info(self, text):
        """
        Extract information from corrigendum documents.
        
        Args:
            text: Extracted OCR text
            
        Returns:
            dict: Extracted information
        """
        import re
        
        # Initialize result dictionary
        result = {
            'success': True,
            'tender_id': None,
            'corrigendum_no': None,
            'original_date': None,
            'revised_date': None,
            'changes': [],
        }
        
        # Extract tender ID
        tender_id_match = re.search(r'(?:Tender|Bid)\s+(?:ID|No|Number|Ref|Reference)\s*:?\s*([A-Z0-9-/]+)', text, re.IGNORECASE)
        if tender_id_match:
            result['tender_id'] = tender_id_match.group(1).strip()
        
        # Extract corrigendum number
        corr_match = re.search(r'Corrigendum\s+(?:No|Number)\s*:?\s*(\d+)', text, re.IGNORECASE)
        if corr_match:
            result['corrigendum_no'] = int(corr_match.group(1))
        
        # Extract original date
        orig_date_match = re.search(r'(?:Original|Earlier|Previous)\s+(?:Date|Time)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', text, re.IGNORECASE)
        if orig_date_match:
            result['original_date'] = orig_date_match.group(1).strip()
        
        # Extract revised date
        revised_date_match = re.search(r'(?:Revised|New|Extended)\s+(?:Date|Time)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', text, re.IGNORECASE)
        if revised_date_match:
            result['revised_date'] = revised_date_match.group(1).strip()
        
        # Extract changes (simplified - would be more sophisticated in real implementation)
        # Look for sections that mention changes, amendments, or modifications
        change_sections = re.findall(r'(?:Change|Amendment|Modification|Revision)\s+\d+\s*:?\s*(.+?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        if change_sections:
            result['changes'] = [section.strip() for section in change_sections]
        
        return result
    
    def _extract_generic_info(self, text):
        """
        Extract generic information from documents.
        
        Args:
            text: Extracted OCR text
            
        Returns:
            dict: Extracted information
        """
        import re
        
        # Initialize result dictionary
        result = {
            'success': True,
            'reference_numbers': [],
            'dates': [],
            'monetary_values': [],
            'organizations': [],
            'email_addresses': [],
            'phone_numbers': [],
        }
        
        # Extract reference numbers (IDs, tender numbers, etc.)
        ref_matches = re.findall(r'(?:ID|No|Number|Ref|Reference)\s*:?\s*([A-Z0-9-/]+)', text, re.IGNORECASE)
        if ref_matches:
            result['reference_numbers'] = [match.strip() for match in ref_matches]
        
        # Extract dates
        date_matches = re.findall(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})', text, re.IGNORECASE)
        if date_matches:
            result['dates'] = [match.strip() for match in date_matches]
        
        # Extract monetary values
        money_matches = re.findall(r'(?:Rs\.?|INR|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', text)
        if money_matches:
            result['monetary_values'] = []
            for match in money_matches:
                # Remove commas and convert to float
                try:
                    value = float(match.replace(',', ''))
                    # Filter out small numbers that are likely not monetary values
                    if value >= 100:  # Arbitrary threshold
                        result['monetary_values'].append(value)
                except ValueError:
                    pass
        
        # Extract email addresses
        email_matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        if email_matches:
            result['email_addresses'] = email_matches
        
        # Extract phone numbers
        phone_matches = re.findall(r'(?:Phone|Mobile|Tel|Contact)?\s*(?:No|Number)?\s*:?\s*(\+?\d[\d\s-]{8,})', text, re.IGNORECASE)
        if phone_matches:
            result['phone_numbers'] = [match.strip() for match in phone_matches]
        
        # Extract organizations (simple approach - would be more sophisticated in real implementation)
        org_matches = re.findall(r'(?:Organization|Authority|Department|Ministry)\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if org_matches:
            result['organizations'] = [match.strip() for match in org_matches]
        
        return result
