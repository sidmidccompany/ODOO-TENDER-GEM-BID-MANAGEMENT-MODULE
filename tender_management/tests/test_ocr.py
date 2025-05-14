from odoo.tests.common import TransactionCase, tagged
from unittest.mock import patch, MagicMock
import base64


@tagged('post_install', '-at_install', 'external')
class TestOCR(TransactionCase):
    
    def setUp(self):
        super(TestOCR, self).setUp()
        
        # Create test attachment
        self.attachment_data = base64.b64encode(b'Fake PDF content with tender details')
        self.attachment = self.env['ir.attachment'].create({
            'name': 'test_tender_document.pdf',
            'datas': self.attachment_data,
            'res_model': 'tender.tender',
            'res_id': 0,  # Will be updated when tender is created
            'mimetype': 'application/pdf',
        })
        
        # Create test tender
        self.tender = self.env['tender.tender'].create({
            'name': 'OCR Test Tender',
            'reference': 'OCR-2024-001',
            'tender_type_id': self.env['tender.type'].create({'name': 'Services', 'code': 'SRV'}).id,
            'submission_deadline': '2024-12-31 23:59:59',
            'estimated_value': 5000.00,
            'currency_id': self.env.ref('base.USD').id,
        })
        
        # Update attachment
        self.attachment.write({'res_id': self.tender.id})
    
    @patch('odoo.addons.tender_management.external.ocr_service.ocr_processor.OCRProcessor.process_document')
    def test_ocr_document_extraction(self, mock_process_document):
        """Test OCR document extraction"""
        # Mock OCR response
        mock_ocr_result = {
            'extracted_text': 'Tender Reference: OCR-2024-001\nSubmission Deadline: 31/12/2024\nEstimated Value: $5,000\nDescription: This is a test tender for OCR services',
            'extracted_fields': {
                'reference': 'OCR-2024-001',
                'deadline': '31/12/2024',
                'value': 5000,
                'description': 'This is a test tender for OCR services',
            }
        }
        mock_process_document.return_value = mock_ocr_result
        
        # Process document with OCR
        self.env['tender.ocr.wizard'].create({
            'tender_id': self.tender.id,
            'attachment_id': self.attachment.id,
        }).action_process_document()
        
        # Check that tender was updated with extracted information
        self.assertEqual(
            self.tender.description, 
            'This is a test tender for OCR services',
            "Tender description not updated from OCR"
        )
    
    @patch('odoo.addons.tender_management.external.ocr_service.ocr_processor.OCRProcessor.extract_table_data')
    def test_ocr_table_extraction(self, mock_extract_table_data):
        """Test OCR table data extraction"""
        # Mock table extraction response
        mock_table_data = [
            ['Item', 'Quantity', 'Unit Price', 'Total'],
            ['Laptop', '10', '1000', '10000'],
            ['Desktop', '5', '800', '4000'],
            ['Printer', '2', '300', '600'],
        ]
        mock_extract_table_data.return_value = mock_table_data
        
        # Process table with OCR
        wizard = self.env['tender.ocr.table.wizard'].create({
            'tender_id': self.tender.id,
            'attachment_id': self.attachment.id,
        })
        
        wizard.action_extract_table()
        
        # Check that line items were created
        tender_items = self.env['tender.item'].search([('tender_id', '=', self.tender.id)])
        self.assertEqual(len(tender_items), 3, "Wrong number of tender items created")
        
        # Verify first item
        laptop_item = tender_items.filtered(lambda i: i.name == 'Laptop')
        self.assertEqual(laptop_item.quantity, 10, "Wrong quantity for laptop item")
        self.assertEqual(laptop_item.unit_price, 1000, "Wrong unit price for laptop item")
    
    def test_document_format_validation(self):
        """Test validation of document formats for OCR processing"""
        # Create invalid attachment (non-PDF)
        invalid_attachment = self.env['ir.attachment'].create({
            'name': 'invalid_document.xyz',
            'datas': base64.b64encode(b'Invalid content'),
            'res_model': 'tender.tender',
            'res_id': self.tender.id,
            'mimetype': 'application/octet-stream',
        })
        
        # Attempt to process invalid document
        wizard = self.env['tender.ocr.wizard'].create({
            'tender_id': self.tender.id,
            'attachment_id': invalid_attachment.id,
        })
        
        with self.assertRaises(Exception):
            wizard.action_process_document()
