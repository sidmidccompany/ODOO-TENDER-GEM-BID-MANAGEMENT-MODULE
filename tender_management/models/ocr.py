# models/ocr.py
import base64
import logging
import tempfile
import os
from datetime import datetime
import re
import PyPDF2
import pytesseract
from PIL import Image
import io

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class TenderOCR(models.Model):
    _name = 'tender.ocr'
    _description = 'Tender OCR Processing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    document_id = fields.Many2one('tender.document', string='Document', required=True, ondelete='cascade')
    tender_id = fields.Many2one('tender.tender', string='Tender', required=True, ondelete='cascade')
    
    # OCR Content
    content = fields.Text(string='OCR Content')
    content_html = fields.Html(string='Formatted Content', compute='_compute_content_html', store=True)
    
    # Extracted Data
    extracted_data = fields.Text(string='Extracted Data')
    extracted_data_json = fields.Text(string='Extracted Data (JSON)')
    
    # Processing Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('done', 'Completed'),
        ('failed', 'Failed')
    ], string='Status', default='draft', tracking=True)
    processing_date = fields.Datetime(string='Processing Date')
    completion_date = fields.Datetime(string='Completion Date')
    
    # Error Handling
    error_message = fields.Text(string='Error Message')
    
    # Confidence Score
    confidence_score = fields.Float(string='Confidence Score', help="OCR confidence score (0-100)")
    
    # Extracted Key Information
    submission_deadline = fields.Datetime(string='Extracted Submission Deadline')
    tender_value = fields.Float(string='Extracted Tender Value')
    tender_id_number = fields.Char(string='Extracted Tender ID')
    issuing_authority = fields.Char(string='Extracted Issuing Authority')
    
    # Additional Fields
    notes = fields.Html(string='Notes')
    
    @api.depends('document_id', 'state')
    def _compute_name(self):
        for record in self:
            if record.document_id:
                record.name = f"OCR: {record.document_id.name} ({record.state})"
            else:
                record.name = f"New OCR Processing ({record.state})"
    
    @api.depends('content')
    def _compute_content_html(self):
        for record in self:
            if not record.content:
                record.content_html = False
                continue
            
            # Convert plain text to HTML with basic formatting
            html_content = record.content.replace('\n', '<br/>')
            
            # Highlight key information
            patterns = {
                r'\b(deadline|submission date|closing date)\b': '<span style="background-color: #FFFF00;">\\1</span>',
                r'\b(estimated value|tender value|budget|cost)\b': '<span style="background-color: #AAFFAA;">\\1</span>',
                r'\b(tender number|tender id|reference number)\b': '<span style="background-color: #AAAAFF;">\\1</span>',
                r'\b(issuing authority|issuer|department|ministry)\b': '<span style="background-color: #FFAAAA;">\\1</span>'
            }
            
            for pattern, replacement in patterns.items():
                html_content = re.sub(pattern, replacement, html_content, flags=re.IGNORECASE)
            
            record.content_html = f'<div style="font-family: monospace;">{html_content}</div>'
    
    def action_process(self):
        """Process document with OCR"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_("This document has already been processed"))
        
        # Update state and processing date
        self.write({
            'state': 'processing',
            'processing_date': fields.Datetime.now()
        })
        
        try:
            # Process document
            self._process_document()
            
            # Extract key information
            self._extract_key_information()
            
            # Update tender with extracted information if confidence is high enough
            if self.confidence_score >= 75.0:
                self._update_tender_information()
            
            # Update state and completion date
            self.write({
                'state': 'done',
                'completion_date': fields.Datetime.now()
            })
            
        except Exception as e:
            _logger.error("OCR processing error: %s", str(e))
            self.write({
                'state': 'failed',
                'error_message': str(e),
                'completion_date': fields.Datetime.now()
            })
    
    def _process_document(self):
        """Process document with OCR to extract text"""
        if not self.document_id or not self.document_id.file:
            raise UserError(_("No document file available for OCR processing"))
        
        # Get file data
        file_data = base64.b64decode(self.document_id.file)
        file_name = self.document_id.file_name or 'document'
        
        # Process based on file extension
        file_ext = os.path.splitext(file_name)[1].lower() if file_name else ''
        
        if file_ext in ('.pdf', '.PDF'):
            content = self._process_pdf(file_data)
        elif file_ext in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'):
            content = self._process_image(file_data)
        else:
            content = self._process_text(file_data)
        
        self.content = content
    
    def _process_pdf(self, file_data):
        """Process PDF file with OCR"""
        content = ""
        confidence = 0
        pages_processed = 0
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        
        try:
            # Open PDF file
            with open(temp_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    
                    # Try to extract text directly from PDF
                    page_text = page.extract_text()
                    
                    # If no text found or text is too short, use OCR
                    if not page_text or len(page_text) < 100:
                        # Convert PDF page to image
                        images = self._pdf_page_to_image(file_data, page_num)
                        
                        # Process each image with OCR
                        page_text = ""
                        page_confidence = 0
                        
                        for img in images:
                            img_text, img_confidence = self._ocr_image(img)
                            page_text += img_text + "\n"
                            page_confidence += img_confidence
                        
                        if images:
                            page_confidence /= len(images)
                        
                        confidence += page_confidence
                    else:
                        # Assume high confidence for embedded text
                        confidence += 95.0
                    
                    content += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                    pages_processed += 1
            
            # Calculate average confidence
            self.confidence_score = confidence / pages_processed if pages_processed > 0 else 0
            
        except Exception as e:
            _logger.error("Error processing PDF: %s", str(e))
            raise UserError(_("Error processing PDF: %s") % str(e))
        finally:
            # Remove temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return content
    
    def _pdf_page_to_image(self, file_data, page_num):
        """Convert PDF page to image for OCR processing"""
        # This is a placeholder - in a real implementation, you would:
        # 1. Use a library like pdf2image or wand to convert PDF page to image
        # 2. Return a list of image objects
        
        # For demonstration, we'll just return an empty list
        # Actual implementation would depend on the specific libraries available
        return []
    
    def _process_image(self, file_data):
        """Process image file with OCR"""
        try:
            # Open image
            img = Image.open(io.BytesIO(file_data))
            
            # Process with OCR
            text, confidence = self._ocr_image(img)
            
            # Update confidence score
            self.confidence_score = confidence
            
            return text
        except Exception as e:
            _logger.error("Error processing image: %s", str(e))
            raise UserError(_("Error processing image: %s") % str(e))
    
    def _ocr_image(self, img):
        """Process image with OCR and return text and confidence score"""
        try:
            # Process with pytesseract
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Extract text
            text = pytesseract.image_to_string(img)
            
            # Calculate confidence
            if 'conf' in ocr_data and ocr_data['conf']:
                confidences = [conf for conf in ocr_data['conf'] if conf != -1]
                confidence = sum(confidences) / len(confidences) if confidences else 0
            else:
                confidence = 0
            
            return text, confidence
        except Exception as e:
            _logger.error("OCR processing error: %s", str(e))
            return "", 0
    
    def _process_text(self, file_data):
        """Process text file"""
        try:
            # Decode file data
            text = file_data.decode('utf-8')
            
            # Set high confidence for text files
            self.confidence_score = 100.0
            
            return text
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'iso-8859-1', 'windows-1252']:
                try:
                    text = file_data.decode(encoding)
                    self.confidence_score = 100.0
                    return text
                except UnicodeDecodeError:
                    continue
            
            # If all decodings fail, raise error
            raise UserError(_("Could not decode text file. The file might be in an unsupported format."))
    
    def _extract_key_information(self):
        """Extract key information from OCR content"""
        if not self.content:
            return
        
        # Extract submission deadline
        self._extract_submission_deadline()
        
        # Extract tender value
        self._extract_tender_value()
        
        # Extract tender ID
        self._extract_tender_id()
        
        # Extract issuing authority
        self._extract_issuing_authority()
        
        # Prepare extracted data summary
        extracted_data = []
        
        if self.submission_deadline:
            extracted_data.append(f"Submission Deadline: {self.submission_deadline}")
        
        if self.tender_value:
            extracted_data.append(f"Tender Value: {self.tender_value}")
        
        if self.tender_id_number:
            extracted_data.append(f"Tender ID: {self.tender_id_number}")
        
        if self.issuing_authority:
            extracted_data.append(f"Issuing Authority: {self.issuing_authority}")
        
        self.extracted_data = "\n".join(extracted_data)
        
        # Prepare JSON data
        self.extracted_data_json = self._prepare_extracted_data_json()
    
    def _extract_submission_deadline(self):
        """Extract submission deadline from content"""
        if not self.content:
            return
        
        # Define patterns for date extraction
        date_patterns = [
            # Common date formats with day, month, year
            r'(?:submission|closing|deadline)[^\n]*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:submission|closing|deadline)[^\n]*?(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            
            # Dates with time
            r'(?:submission|closing|deadline)[^\n]*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+\d{1,2}:\d{2}(?:\s*[AP]M)?)',
            r'(?:submission|closing|deadline)[^\n]*?(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\s+\d{1,2}:\d{2}(?:\s*[AP]M)?)',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            if matches:
                # Take the first match
                date_str = matches[0]
                
                # Try to parse the date
                try:
                    # For demonstration, we use a simple approach
                    # In a real implementation, you would use a more robust date parser
                    dt = datetime.strptime(date_str, '%d/%m/%Y')
                    self.submission_deadline = dt
                    return
                except ValueError:
                    # Try alternative formats
                    try:
                        dt = datetime.strptime(date_str, '%d-%m-%Y')
                        self.submission_deadline = dt
                        return
                    except ValueError:
                        # Continue to next match
                        continue
    
    def _extract_tender_value(self):
        """Extract tender value from content"""
        if not self.content:
            return
        
        # Define patterns for value extraction
        value_patterns = [
            r'(?:estimated|tender|contract)\s+value\s*(?::|is|of)?\s*(?:[A-Z]{3}|[₹$€£])?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
            r'(?:budget|cost)\s*(?::|is|of)?\s*(?:[A-Z]{3}|[₹$€£])?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
            r'value\s*:\s*(?:[A-Z]{3}|[₹$€£])?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)'
        ]
        
        for pattern in value_patterns:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            if matches:
                # Take the first match
                value_str = matches[0]
                
                # Remove commas and convert to float
                value_str = value_str.replace(',', '')
                try:
                    value = float(value_str)
                    self.tender_value = value
                    return
                except ValueError:
                    # Continue to next match
                    continue
    
    def _extract_tender_id(self):
        """Extract tender ID from content"""
        if not self.content:
            return
        
        # Define patterns for tender ID extraction
        id_patterns = [
            r'(?:tender|bid|ref(?:erence)?)\s*(?:no|number|id)\.?\s*:?\s*([A-Z0-9-_/]+)',
            r'(?:tender|bid|ref(?:erence)?)\s*(?:no|number|id)\.?\s*([A-Z0-9-_/]+)',
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            if matches:
                # Take the first match
                tender_id = matches[0]
                self.tender_id_number = tender_id.strip()
                return
    
    def _extract_issuing_authority(self):
        """Extract issuing authority from content"""
        if not self.content:
            return
        
        # Define patterns for issuing authority extraction
        authority_patterns = [
            r'(?:issuing|procuring)\s+authority\s*:?\s*([^\n]+)',
            r'(?:issued|procured)\s+by\s*:?\s*([^\n]+)',
            r'(?:department|ministry|organization)\s*:?\s*([^\n]+)',
        ]
        
        for pattern in authority_patterns:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            if matches:
                # Take the first match
                authority = matches[0]
                self.issuing_authority = authority.strip()
                return
    
    def _prepare_extracted_data_json(self):
        """Prepare extracted data in JSON format"""
        import json
        
        data = {
            'submission_deadline': self.submission_deadline.isoformat() if self.submission_deadline else None,
            'tender_value': self.tender_value,
            'tender_id': self.tender_id_number,
            'issuing_authority': self.issuing_authority,
            'confidence_score': self.confidence_score
        }
        
        return json.dumps(data)
    
    def _update_tender_information(self):
        """Update tender with extracted information"""
        if not self.tender_id:
            return
        
        update_vals = {}
        
        # Update submission deadline if extracted
        if self.submission_deadline and not self.tender_id.submission_date:
            update_vals['submission_date'] = self.submission_deadline
        
        # Update tender value if extracted
        if self.tender_value and not self.tender_id.tender_value:
            update_vals['tender_value'] = self.tender_value
        
        # Update issuing authority if extracted
        if self.issuing_authority and not self.tender_id.issuing_authority:
            update_vals['issuing_authority'] = self.issuing_authority
        
        if update_vals:
            self.tender_id.write(update_vals)
    
    def action_reset(self):
        """Reset OCR processing"""
        self.ensure_one()
        
        if self.state in ['done', 'failed']:
            self.write({
                'state': 'draft',
                'content': False,
                'extracted_data': False,
                'extracted_data_json': False,
                'error_message': False,
                'processing_date': False,
                'completion_date': False,
                'confidence_score': 0.0,
                'submission_deadline': False,
                'tender_value': 0.0,
                'tender_id_number': False,
                'issuing_authority': False
            })
    
    def action_view_document(self):
        """View the original document"""
        self.ensure_one()
        return {
            'name': _('Document'),
            'view_mode': 'form',
            'res_model': 'tender.document',
            'res_id': self.document_id.id,
            'type': 'ir.actions.act_window'
        }
    
    def action_view_tender(self):
        """View the related tender"""
        self.ensure_one()
        return {
            'name': _('Tender'),
            'view_mode': 'form',
            'res_model': 'tender.tender',
            'res_id': self.tender_id.id,
            'type': 'ir.actions.act_window'
        }
