
# File: tender_management/tests/test_tender.py
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
import datetime


@tagged('post_install', '-at_install')
class TestTender(TransactionCase):
    
    def setUp(self):
        super(TestTender, self).setUp()
        
        # Create test users
        self.tender_manager = self.env['res.users'].create({
            'name': 'Tender Manager',
            'login': 'tender_manager@test.com',
            'groups_id': [(4, self.env.ref('tender_management.group_tender_manager').id)]
        })
        
        self.tender_user = self.env['res.users'].create({
            'name': 'Tender User',
            'login': 'tender_user@test.com',
            'groups_id': [(4, self.env.ref('tender_management.group_tender_user').id)]
        })
        
        # Create test tender type
        self.tender_type = self.env['tender.type'].create({
            'name': 'Construction',
            'code': 'CONST',
        })
        
        # Create test tender
        self.tender = self.env['tender.tender'].with_user(self.tender_manager).create({
            'name': 'Test Construction Tender',
            'reference': 'TCT-2024-001',
            'tender_type_id': self.tender_type.id,
            'submission_deadline': datetime.datetime.now() + datetime.timedelta(days=30),
            'estimated_value': 10000.00,
            'currency_id': self.env.ref('base.USD').id,
        })
    
    def test_tender_creation(self):
        """Test that tenders are created correctly"""
        self.assertEqual(self.tender.state, 'draft', "New tender should be in draft state")
        self.assertEqual(self.tender.name, 'Test Construction Tender', "Tender name not set correctly")
        self.assertEqual(self.tender.tender_type_id, self.tender_type, "Tender type not set correctly")
    
    def test_tender_state_changes(self):
        """Test tender state workflow"""
        # Publish the tender
        self.tender.action_publish()
        self.assertEqual(self.tender.state, 'published', "Tender should be in published state")
        
        # Submit a bid
        self.env['tender.bid'].create({
            'tender_id': self.tender.id,
            'partner_id': self.env['res.partner'].create({'name': 'Test Vendor'}).id,
            'amount': 9500.00,
            'currency_id': self.env.ref('base.USD').id,
            'technical_score': 80,
        })
        
        # Close the tender
        self.tender.action_close()
        self.assertEqual(self.tender.state, 'closed', "Tender should be in closed state")
        
        # Award the tender
        self.tender.action_award()
        self.assertEqual(self.tender.state, 'awarded', "Tender should be in awarded state")
    
    def test_deadline_validation(self):
        """Test deadline validation rules"""
        # Try to create a tender with a past deadline
        with self.assertRaises(ValidationError):
            self.env['tender.tender'].with_user(self.tender_manager).create({
                'name': 'Invalid Deadline Tender',
                'reference': 'TCT-2024-002',
                'tender_type_id': self.tender_type.id,
                'submission_deadline': datetime.datetime.now() - datetime.timedelta(days=1),
                'estimated_value': 10000.00,
                'currency_id': self.env.ref('base.USD').id,
            })
    
    def test_user_access_rights(self):
        """Test user access rights for tender management"""
        # Tender user should be able to read but not create tenders
        self.tender.with_user(self.tender_user).read()
        
        with self.assertRaises(Exception):
            self.env['tender.tender'].with_user(self.tender_user).create({
                'name': 'No Permission Tender',
                'reference': 'TCT-2024-003',
                'tender_type_id': self.tender_type.id,
                'submission_deadline': datetime.datetime.now() + datetime.timedelta(days=30),
                'estimated_value': 10000.00,
                'currency_id': self.env.ref('base.USD').id,
            })
